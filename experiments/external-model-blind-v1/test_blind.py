import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_blind as p

class ExternalBlindTests(unittest.TestCase):
    def setUp(self):
        self.seed=p.CFG["seeds"][0]
        self.case={"id":self.seed["id"],"title":"Pequeño taller",
           "question":"¿Qué mecanismos causales se justifican?",
           "facts":[{"id":"F1","text":"El producto acabado se conserva en el almacén de la empresa."},
                    {"id":"F2","text":"Los encargos confirmados pendientes esperan para despacharse desde estas existencias."},
                    {"id":"F3","text":"Los envíos quitan unidades del almacén y cancelan compromisos de entregar."}]}
    def test_pilot_sources_unchanged(self):
        p.verify_frozen()
    def test_three_distinct_models(self):
        self.assertNotEqual(p.CFG["generator_model"],p.CFG["reviewer_model"])
        self.assertNotEqual(p.CFG["reviewer_model"],p.CFG["tested_model"])
        self.assertNotEqual(p.CFG["tested_model"],p.CFG["generator_model"])
    def test_twenty_four_unique_seeds(self):
        self.assertEqual(len(p.CFG["seeds"]),24)
        self.assertEqual(len({x["id"] for x in p.CFG["seeds"]}),24)
    def test_generate_case_accepts_qualitative_fact_list(self):
        r={"title":"Taller de piezas","question":"¿Cómo funciona el negocio?",
           "facts":[x["text"] for x in self.case["facts"]]}
        self.assertEqual(p.parse_case(self.seed,json.dumps(r))["facts"][1]["id"],"F2")
    def test_no_numeric_facts(self):
        d={"title":"Taller","question":"¿Cómo funciona?",
           "facts":["La planta produce 12 unidades por hora.","Una oración de entrada con texto suficiente en español.",
                    "Otra oración sobre un almacén de producto terminado."]}
        with self.assertRaisesRegex(ValueError,"CASE_HAS_NUMBERS"):p.parse_case(self.seed,json.dumps(d))
    def test_reject_invented_molecule_in_external_label(self):
        x={"label_status":"DETERMINATE","molecules":["MAGIC_QUEUE"],
          "support":[],"reason":"La estructura sería una cola."}
        with self.assertRaisesRegex(ValueError,"REFERENCE_MOLECULES"):
            p.parse_reference(self.case,json.dumps(x))
    def test_require_exact_positive_literal_citation(self):
        x={"label_status":"DETERMINATE","molecules":["BACKLOG_FLOW"],
           "support":[{"target":"BACKLOG_FLOW","fact_id":"F2","quote":"falsificación literal inexistente"}],
           "reason":"Hay inventario de terminado y pedidos confirmados por despachar."}
        with self.assertRaisesRegex(ValueError,"REFERENCE_CITATION_NOT_LITERAL"):
            p.parse_reference(self.case,json.dumps(x))
        x["support"][0]["quote"]="Los encargos confirmados pendientes esperan para despacharse"
        v=p.parse_reference(self.case,json.dumps(x))
        self.assertEqual(v["supported_facts"]["BACKLOG_FLOW"],["F2"])
    def test_indeterminate_not_used_as_invented_truth(self):
        x={"label_status":"INDETERMINATE","molecules":[],"support":[],
          "reason":"Existe una contradicción sin resolver."}
        self.assertIsNone(p.parse_reference(self.case,json.dumps(x)))
    def test_original_prompts_never_contain_glm_labels(self):
        for arm in p.old_prompt.ARMS:
            messages=p.old_prompt.messages(self.case,arm)
            s=json.dumps(messages,ensure_ascii=False)
            self.assertNotIn("supported_facts",s)
            self.assertNotIn("proxy_reference",s)
            self.assertNotIn("label_status",s)
    def test_same_original_scorer(self):
        self.assertTrue(callable(p.old_eval.summarize))
        self.assertTrue(callable(p.old_base.respond))
if __name__=="__main__":unittest.main()

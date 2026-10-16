import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from compile_graph import read,verify,render
from run_llm import prompt,SYSTEM,CASE_IDS

def oracle():
    return read("oracle_graph_G01.json")

def choice(kind,source=None):
    p=oracle()
    if kind=="STRUCTURE_ONLY":
        p["decision"]="STRUCTURE_ONLY"
        p["numeric_evidence"]=[]
        p["missing"]=["No se conocen capacidad ni tasas ni tiempos de respuesta."]
    return p

class SDGraphAssembly(unittest.TestCase):
    def test_base_graph_is_valid_synthetic(self):
        r=verify("G01",oracle())
        self.assertEqual(r["status"],"READY_FOR_SYNTHETIC_OMC")
        self.assertTrue(r["simulation_authorized"])
        self.assertEqual((r["stocks"],r["flows"],r["material_links"],r["causal_links"]),(3,3,5,2))
    def test_structure_with_missing_parameters_has_no_simulation(self):
        r=verify("G02",choice("STRUCTURE_ONLY"))
        self.assertEqual(r["status"],"STRUCTURE_ONLY")
        self.assertFalse(r["simulation_authorized"])
        self.assertFalse(r["modelica_generated"])
    def test_empty_claims_abstain_when_evidence_does_not_identify_model(self):
        for cid in ("G03","G04"):
            r=verify(cid,{"nodes":[],"material_links":[],"causal_links":[],
                          "feedback_loops":[],"numeric_evidence":[],
                          "decision":"ABSTAIN","missing":["No se conoce estructura compatible."]})
            self.assertEqual(r["status"],"VALID_ABSTENTION")
    def test_reject_unverified_simulation_parameters(self):
        p=oracle();p["numeric_evidence"]=[]
        self.assertEqual(verify("G01",p)["reason"],"NO_VERIFIED_COMPLETE_SYNTHETIC_INPUTS")
        p=choice("STRUCTURE_ONLY");p["decision"]="SIMULATE_SYNTHETIC";p["numeric_evidence"]=["F4"]
        self.assertEqual(verify("G02",p)["reason"],"NO_VERIFIED_COMPLETE_SYNTHETIC_INPUTS")
    def test_reject_wrong_stock_flow_types(self):
        p=oracle();p["nodes"][1]["kind"]="flow"
        self.assertEqual(verify("G01",p)["reason"],"STOCK_FLOW_TYPE_MISMATCH")
    def test_reject_invented_connection_or_missing_flow(self):
        p=oracle();p["material_links"][3]["target"]="incoming_orders"
        self.assertEqual(verify("G01",p)["status"],"REJECTED")
        p=oracle();p["material_links"].pop()
        self.assertEqual(verify("G01",p)["reason"],"INCOMPLETE_MATERIAL_FLOW")
    def test_reject_unjustified_links_and_polarity(self):
        p=oracle();p["causal_links"][0]["polarity"]="-"
        self.assertEqual(verify("G01",p)["reason"],"UNSUPPORTED_CAUSAL_POLARITY_OR_CITATION")
        p=oracle();p["material_links"][1]["evidence"]=["F4"]
        self.assertEqual(verify("G01",p)["reason"],"UNSUPPORTED_OR_UNGROUNDED_MATERIAL_LINK")
    def test_reject_invented_feedback(self):
        p=oracle();p["feedback_loops"][0]["path"]=["incoming_orders","preparation","incoming_orders"]
        self.assertEqual(verify("G01",p)["reason"],"UNSUPPORTED_OR_DUPLICATE_FEEDBACK_LOOP")
    def test_prompt_has_better_sd_reasoning_but_no_equation_generation(self):
        s=SYSTEM.lower()
        for v in ("acumulaciones","retroalimentación","polaridad","evidencia","openmodelica"):
            self.assertIn(v,s)
        self.assertIn("no generes fórmulas",s)
        prompts=[json.dumps(prompt(c),ensure_ascii=False) for c in read("cases_public.json")["cases"]]
        for s in prompts:
            self.assertNotIn("oracle_graph_G01",s)
            self.assertNotIn("fixtures",s)
            self.assertNotIn("answer_key",s)
    def test_assembly_uses_existing_components_and_no_derivative_formula(self):
        code=render(oracle())
        self.assertNotIn("der(",code)
        self.assertNotIn("min(",code)
        self.assertNotIn("max(",code)
        self.assertNotIn("function",code)
        self.assertEqual(code.count("connect("),7)
        self.assertEqual(code.count("SystemDynamics.Levels.Level "),2)
        self.assertEqual(code.count("SystemDynamics.Levels.Level1a "),1)
        self.assertEqual(code.count("SystemDynamics.Rates.RRate "),2)
        self.assertIn("Modelica.Blocks.Math.Gain preparation_response",code)
        self.assertIn("connect(preparation_response.y,preparation.u)",code)
    def test_graph_labels_are_never_interpolated_as_source_code(self):
        p=oracle();p["nodes"][0]["label"]='Evil ); system("remove all");'
        self.assertEqual(verify("G01",p)["status"],"READY_FOR_SYNTHETIC_OMC")
        result=render(p)
        self.assertNotIn("Evil",result)
        self.assertNotIn("system(",result)
    def test_nonobject_or_code_response_is_rejected(self):
        self.assertEqual(verify("G01","some code")["status"],"REJECTED")
        p=oracle();p["ModelicaCode"]="der(stock)=123"
        self.assertEqual(verify("G01",p)["reason"],"INVALID_RESPONSE_SCHEMA")
    def test_component_sources_are_actual_green_reference(self):
        root=HERE.parents[1]
        self.assertTrue((root/"experiments/openmodelica-mto-s2/IGCS2MakeToOrder.mo").exists())
        self.assertEqual(tuple(c["id"] for c in read("cases_public.json")["cases"]),CASE_IDS)
    def test_empty_missing_information_does_not_pass_structure_only(self):
        p=choice("STRUCTURE_ONLY");p["missing"]=[]
        self.assertEqual(verify("G02",p)["reason"],"STRUCTURE_ONLY_NEEDS_OPEN_QUESTIONS")

if __name__=="__main__":unittest.main()

import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import compose,run_study
def graph(cid,policy):
    fs=compose.load_case(cid)["facts"]
    q=lambda i:{"fact_id":fs[i]["id"],"quote":fs[i]["text"]}
    return {"decision":"COMPOSE","policy":policy,
      "instances":[{"id":"accepted","module":"SOURCE","evidence":q(0)},
                   {"id":"factory","module":policy,"evidence":q(1)},
                   {"id":"delivered","module":"SINK","evidence":q(2)}],
      "links":[{"from":"accepted.out","to":"factory.in","evidence":q(0)},
               {"from":"factory.out","to":"delivered.in","evidence":q(2)}],
      "support":[q(0)],"counterevidence":[q(2)],"unresolved":[]}
class ChoiceTests(unittest.TestCase):
    def test_both_semantically_different_policies_have_same_external_types(self):
        catalog=compose.read("catalog.json")
        signatures=catalog["interfaces"]
        self.assertEqual(signatures["MTO"],signatures["MTS"])
        self.assertNotEqual(compose.ALLOWED["MTO"],compose.ALLOWED["MTS"])
    def test_mto_and_mts_both_pass_same_typed_ports(self):
        for policy in ("MTO","MTS"):
            p=graph("T01",policy)
            self.assertEqual(compose.validate("T01",p)["status"],"STRUCTURALLY_VALID")
    def test_render_returns_genuinely_different_native_models(self):
        a=compose.render("T01",graph("T01","MTO"))
        b=compose.render("T01",graph("T01","MTS"))
        self.assertNotEqual(a,b)
        self.assertIn("IGCS2MakeToOrder.Components",a)
        self.assertIn("IGCS1Parity.Components",b)
        self.assertNotIn("der(",a+b)
    def test_gold_is_not_a_gate_for_a_wrong_choice(self):
        self.assertEqual(compose.read("evaluation_gold.json")["cases"]["T01"]["policy"],"MTO")
        self.assertTrue(compose.validate("T01",graph("T01","MTS"))["executable"])
    def test_zero_order_probe_uses_distinct_original_models(self):
        file=(HERE/"BehaviorProbes.mo").read_text()
        self.assertIn("extends IGCS2MakeToOrder.Components",file)
        self.assertIn("extends IGCS1Parity.Components",file)
        self.assertIn("acceptedOrders=0",file)
        self.assertIn("beforeRush=0",file)
    def test_invented_module_rejected(self):
        p=graph("T01","MTO");p["instances"][1]["module"]="MAGIC_DELAY"
        self.assertIn("M_UNKNOWN_MODULE",{e["code"] for e in compose.validate("T01",p)["issues"]})
    def test_wrong_ports_fail(self):
        p=graph("T01","MTO");p["links"][1]["to"]="accepted.out"
        self.assertIn("T_WRONG_PORT",{e["code"] for e in compose.validate("T01",p)["issues"]})
    def test_literal_fake_quote_rejected(self):
        p=graph("T01","MTO")
        p["support"]=[{"fact_id":"F1","quote":"fabricamos sin ningun pedido para almacenes"}]
        self.assertIn("E_QUOTE_INVALID",{e["code"] for e in compose.validate("T01",p)["issues"]})
    def test_abstention_is_a_real_first_class_result(self):
        p={"decision":"ABSTAIN","policy":None,"instances":[],"links":[],"support":[],
          "counterevidence":[],"unresolved":["CONFLICTING_POLICIES"]}
        r=compose.validate("T11",p)
        self.assertEqual(r["status"],"ABSTAIN")
        self.assertEqual(run_study.label(p),"CONTRADICTORY")
        with self.assertRaises(ValueError):compose.render("T11",p)
    def test_must_supply_counterevidence(self):
        p=graph("T05","MTS");p["counterevidence"]=[]
        self.assertIn("E_RIVAL_EXCLUSION_MISSING",{e["code"] for e in compose.validate("T05",p)["issues"]})
    def test_no_numbers_or_gold_leaked_into_prompt(self):
        msgs=run_study.msgs(compose.load_case("T01"),[])
        text=json.dumps(msgs,ensure_ascii=False)
        self.assertNotIn("evaluation_gold",text)
        self.assertNotIn("beforeRush=6",text)
        self.assertNotIn("capacity=12",text)
        self.assertNotIn("der(",text)
    def test_baseline_not_given_golden_answers(self):
        self.assertEqual(len(compose.read("cases.json")["cases"]),12)
        self.assertEqual(len(compose.read("evaluation_gold.json")["cases"]),12)
        self.assertEqual(run_study.type_baseline(compose.load_case("T01")),"INSUFFICIENT_EVIDENCE")
    def test_markdown_fenced_json_transport_is_allowed(self):
        p=graph("T01","MTO")
        fence=chr(96)*3+"json\n"+json.dumps(p)+"\n"+chr(96)*3
        self.assertEqual(run_study.parse(fence),p)
        with self.assertRaises(ValueError):run_study.parse(fence+"\nUna explicacion añadida")
if __name__=="__main__":unittest.main()

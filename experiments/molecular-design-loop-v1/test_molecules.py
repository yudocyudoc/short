import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import compose,run_cycle

def oracle():return json.loads((HERE/"oracle_human_graph.json").read_text(encoding="utf-8"))

class MolecularTopologyTests(unittest.TestCase):
    def test_oracle_is_valid_but_human_not_llm(self):
        result=compose.validate(oracle())
        self.assertEqual(result["status"],"STRUCTURALLY_VALID")
        self.assertEqual(result["validated_material_links"],3)
    def test_native_molecule_source_is_present_and_self_contained(self):
        f=(HERE/"IGCMolecules.mo").read_text()
        self.assertIn("model BoundedQueue",f)
        self.assertIn("SystemDynamics.Levels.Level stock",f)
        self.assertIn("SystemDynamics.Rates.RRate release",f)
        self.assertIn("Modelica.Blocks.Math.Gain response",f)
        self.assertNotIn("der(",f)
    def test_modelica_compilation_output_comes_from_trusted_templates(self):
        p=oracle();src=compose.render(p)
        self.assertIn("IGCMolecules.BoundedQueue preparation",src)
        self.assertIn("IGCMolecules.BoundedQueue dispatch",src)
        self.assertEqual(src.count("connect("),3)
        self.assertNotIn("der(",src)
        self.assertNotIn("min(",src)
    def test_disallow_missing_molecule(self):
        p=oracle();p["instances"].pop()
        r=compose.validate(p)
        self.assertEqual(r["status"],"REPAIRABLE")
        self.assertIn("M_REQUIRED_ROLE_MISSING",{x["code"] for x in r["issues"]})
    def test_disallow_swap_of_semantic_material_ports(self):
        p=oracle();p["links"][0]["to"]="ready.in"
        r=compose.validate(p)
        self.assertIn("T_INCOMPATIBLE_PORT",{x["code"] for x in r["issues"]})
    def test_disallow_invented_native_component(self):
        p=oracle();p["instances"][0]["module"]="BusinessSimulation.Transceivers.Chain"
        self.assertIn("M_UNKNOWN_MOLECULE",{x["code"] for x in compose.validate(p)["issues"]})
    def test_disallow_extra_equations_and_parameters_in_ast(self):
        p=oracle();p["equations"]=["der(stock)=999"]
        self.assertEqual(compose.validate(p)["issues"][0]["code"],"S_SCHEMA")
        with self.assertRaises(ValueError):compose.render(p)
    def test_falsified_evidence_does_not_pass(self):
        p=oracle()
        p["links"][0]["evidence"][0]["quote"]="Invented phrase from imaginary source"
        self.assertIn("E_LINK_UNGROUNDED",{x["code"] for x in compose.validate(p)["issues"]})
    def test_incorrect_stage_citation_does_not_pass(self):
        p=oracle()
        p["instances"][1]["evidence"]=[{"fact_id":"F3","quote":
             "Los trabajos terminados esperan una segunda etapa de reparto."}]
        self.assertIn("E_INSTANCE_UNGROUNDED",{x["code"] for x in compose.validate(p)["issues"]})
    def test_untrusted_identifiers_never_enter_modelica(self):
        p=oracle();p["instances"][0]["id"]="bad);system('x')"
        self.assertEqual(compose.validate(p)["status"],"REPAIRABLE")
        p=oracle();p["instances"][0]["id"]="worksource"
        p["links"][0]["from"]="worksource.out"
        self.assertEqual(compose.validate(p)["status"],"STRUCTURALLY_VALID")
        self.assertNotIn("worksource",compose.render(p))
    def test_feedback_includes_historical_response_and_no_numbers(self):
        result=compose.validate({"instances":[],"links":[],"unresolved":[]})
        messages=run_cycle.prompt([("{}",run_cycle.structural_feedback(result))])
        self.assertEqual([x["role"] for x in messages],["system","user","assistant","user"])
        self.assertNotIn("capacityPreparing=10",json.dumps(messages))
        self.assertNotIn("der(",json.dumps(messages))
    def test_fenced_json_from_real_llama_is_accepted_without_altering_structure(self):
        import json
        p=oracle()
        fence="```json\n"+json.dumps(p,ensure_ascii=False)+"\n```"
        self.assertEqual(run_cycle.parse_proposal_text(fence),p)
        self.assertEqual(run_cycle.parse_proposal_text(json.dumps(p)),p)
        with self.assertRaises(ValueError):
            run_cycle.parse_proposal_text(fence+"\nAdditional prose")
        with self.assertRaises(ValueError):
            run_cycle.parse_proposal_text("```json\n{nonsense}\n```")
    def test_max_five_attempts(self):
        with self.assertRaises(ValueError):run_cycle.run(HERE/"_never",False,6)
    def test_no_uncited_extra_link(self):
        p=oracle();p["links"].append({"from":"orders.out","to":"work.in",
           "evidence":copy.deepcopy(p["links"][0]["evidence"])})
        self.assertIn("T_DUPLICATE_OR_MULTICAST",{x["code"] for x in compose.validate(p)["issues"]})
    def test_missing_links_are_not_autofilled(self):
        p=oracle();p["links"].pop()
        res=compose.validate(p)
        self.assertFalse(res["structure_accepted"])
        self.assertIn("M_MISSING_MATERIAL_LINK",{x["code"] for x in res["issues"]})

if __name__=="__main__":unittest.main()

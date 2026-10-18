"""P2 IR contract tests: structural pass is NOT native execution or causal proof."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import linter

REG=linter.read_registry()

def n(id,cl,role="CUSTOMER",binding="Person",intent=None,evidence=None):
    intents={"boundary-source":"EXOGENOUS_ARRIVAL",
     "conserved-stock":"WAITING_STOCK","boundary-sink":"CONSERVATIVE_EXIT",
     "contact-contagion":"INTERPERSONAL_CONTACT_TRANSMISSION",
     "feedback-policy":"CAPACITY_ADJUSTMENT","capacity-actuator":"CAPACITY_ADJUSTMENT"}
    return {"id":id,"class_id":cl,"binding":binding,"entity_role":role,
            "intent":intent or intents[cl],"evidence":evidence or ["E01"]}

def link(a,b,kind="LINK",adapter=None):
    return {"kind":kind,"from":a,"to":b,"adapter":adapter,"evidence":["E01"]}

def branched():
    return {"schema":"igc-sl/p2.0","instances":[
      n("arrivals","boundary-source"),
      n("waiting","conserved-stock"),
      n("served","boundary-sink"),
      n("left","boundary-sink")
    ],"relations":[
      link("arrivals.out","waiting.in"),
      link("waiting.out_a","served.in"),
      link("waiting.out_b","left.in")
    ],"requested_policies":[]}

def codes(result):return [x["code"] for x in result["issues"]]

class P2Tests(unittest.TestCase):
    def test_pos01_valid_structurally_but_never_executable(self):
        r=linter.lint(branched(),REG)
        self.assertEqual(r["status"],"STRUCTURAL_ONLY",r)
        self.assertTrue(r["structurally_compatible"])
        self.assertFalse(r["executable"])
        self.assertEqual(r["multi_outlet_stock_instances"],["waiting"])
        self.assertIn("NOT_NUMERICALLY_VERIFIED",r["conservation"])

    def test_neg01_duplicate_material_rejected(self):
        g=branched()
        g["relations"][-1]["from"]="waiting.out_a"
        r=linter.lint(g,REG)
        self.assertEqual(r["status"],"INVALID")
        self.assertIn("MATERIAL_DUPLICATION",codes(r))

    def test_pos02_generic_stock_origin_does_not_prevent_customer_transfer(self):
        self.assertEqual(REG["classes"]["conserved-stock"]["origin_domain"],"orders")
        g=branched()
        for x in g["instances"]:x["evidence"]=["E02"]
        for x in g["relations"]:x["evidence"]=["E02"]
        r=linter.lint(g,REG)
        self.assertEqual(r["status"],"STRUCTURAL_ONLY",r)
        self.assertFalse(r["native_class_admitted"])

    def test_neg02_false_friend_purpose_and_no_evidence(self):
        g={"instances":[n("arrivals","boundary-source"),
                        n("carrier","contact-contagion",intent="WAITING_STOCK"),
                        n("left","boundary-sink")],
           "relations":[link("arrivals.out","carrier.in"),
                        link("carrier.out","left.in")]}
        g["instances"][1]["evidence"]=[]
        g["instances"][1]["hypothesis"]=False
        r=linter.lint(g,REG)
        self.assertEqual(r["status"],"INVALID")
        self.assertIn("SEMANTIC_MISMATCH",codes(r))
        self.assertIn("MISSING_EVIDENCE",codes(r))

    def test_neg03_policy_absence_with_structural_feedback(self):
        g=branched()
        g["instances"] += [n("policy","feedback-policy"),
                           n("actuator","capacity-actuator")]
        g["relations"] += [
           link("waiting.level","policy.observed","SENSE","readonly-stock-observation"),
           link("policy.command","actuator.command","GOVERN")
        ]
        g["requested_policies"]=["feedback-policy"]
        r=linter.lint(g,REG)
        self.assertTrue(r["structurally_compatible"],r)
        self.assertEqual(r["status"],"STRUCTURAL_WITH_MISSING_POLICY")
        self.assertIn("POLICY_UNIMPLEMENTED",codes(r))
        self.assertFalse(r["executable"])

    def test_neg04_same_units_and_general_person_type_distinct_roles(self):
        g={"instances":[n("arrivals","boundary-source","CUSTOMER"),
                        n("payroll","boundary-sink","EMPLOYEE")],
           "relations":[link("arrivals.out","payroll.in")]}
        r=linter.lint(g,REG)
        self.assertIn("ENTITY_MISMATCH",codes(r))
        self.assertEqual(r["status"],"INVALID")

    def test_absent_observation_adapter_is_rejected(self):
        g=branched()
        g["instances"].append(n("policy","feedback-policy"))
        g["relations"].append(link("waiting.level","policy.observed","SENSE"))
        g["requested_policies"]=["feedback-policy"]
        r=linter.lint(g,REG)
        self.assertIn("BAD_ADAPTER",codes(r))

    def test_flow_cannot_use_stock_sensor_adapter(self):
        g=branched()
        g["instances"].append(n("policy","feedback-policy"))
        # A rate cannot enter a state sensor with a reused stock adapter.
        g["relations"].append(link("waiting.out_a","policy.observed",
                                   "SENSE","readonly-stock-observation"))
        result=linter.lint(g,REG)
        self.assertIn("BAD_ADAPTER",codes(result))
        self.assertFalse(result["executable"])

    def test_sense_never_transfers_material(self):
        g=branched()
        g["relations"][1]["kind"]="SENSE"
        r=linter.lint(g,REG)
        self.assertIn("TYPE_MISMATCH",codes(r))

    def test_control_is_not_material_flow(self):
        g=branched()
        g["instances"].append(n("policy","feedback-policy"))
        g["relations"].append(link("policy.command","served.in","LINK"))
        r=linter.lint(g,REG)
        self.assertIn("TYPE_MISMATCH",codes(r))

    def test_no_free_numeric_parameters_in_conceptual_ir(self):
        g=branched()
        g["instances"][1]["parameters"]={"maxThroughput":12}
        r=linter.lint(g,REG)
        self.assertIn("PARAMETER_VALUE_FORBIDDEN",codes(r))

    def test_missing_molecule_abstains_instead_of_hallucinating(self):
        g=branched()
        g["instances"][1]["class_id"]="wait-abandonment-law-never-admitted"
        r=linter.lint(g,REG)
        self.assertIn("UNKNOWN_CLASS",codes(r))
        self.assertFalse(r["executable"])

if __name__=="__main__":unittest.main()

#!/usr/bin/env python3
"""IGC0 v2: fixed semantic acceptance tests frozen before second M01 inference."""
import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))
from test_semantic_audit import base,PACKET,REF
from semantic_audit_v2 import audit_v2

ROLES=("shared_kitchen","order_backlog","delivery_dispatch","payout_delay")
def fixture():
    obj=base()
    obj["informational_links"]=[]
    obj["mechanism_checks"]=[
        {"role":role,"status":"unknown","linked_ids":[],"evidence_refs":[],
         "explanation":"No tenemos información operacional para afirmarlo"}
        for role in ROLES]
    obj["actions"]=["no_delivery","open_full","open_offpeak_capped"]
    obj["decision"]={"choice":"abstain","reason":"No existe un motor calibrado","assumptions":[]}
    obj["scenario_projections"]=[]
    return obj
def codes(obj,packet=PACKET):
    return {x["code"] for x in audit_v2(obj,packet)["issues"]}
class TestIGC0V2(unittest.TestCase):
    def test_clean_contract(self):
        self.assertTrue(audit_v2(fixture(),PACKET)["accepted"])
    def test_baseline_model_fails_without_new_fields(self):
        self.assertIn("MISSING_MECHANISM_CHECKS",codes(base()))
    def test_missing_contrast(self):
        m=fixture();m["contrast"]=[]
        self.assertIn("MISSING_IGC_CONTRAST",codes(m))
    def test_contrast_requires_evidence(self):
        m=fixture();m["contrast"][0]["evidence_refs"]=[]
        self.assertIn("NO_EVIDENCE",codes(m))
    def test_contrast_must_link_real_pipe(self):
        m=fixture();m["contrast"][0]["pipe_or_mechanism_id"]="imaginary"
        self.assertIn("UNLINKED_CONTRAST",codes(m))
    def test_hypothesis_none_rejected(self):
        m=fixture();m["contrast"][0]["epistemic"]="HIPÓTESIS"
        self.assertIn("UNSUPPORTED_NO_DEVIATION",codes(m))
    def test_money_to_food_rejected(self):
        m=fixture();m["stocks"].append({"id":"food","unit":"meals_equivalent","initial":None,
                                        "initial_label":"DESCONOCIDO","initial_refs":[]})
        m["pipes"].append({"id":"bad","from":"food","to":"cash","unit_per_time":"MXN/day",
                           "mechanism":"error","evidence_refs":[REF],"epistemic":"OBSERVADO",
                           "capacity_source":None})
        self.assertIn("CROSS_DOMAIN_STOCK_FLOW",codes(m))
    def test_mechanism_names_required(self):
        m=fixture();m["mechanism_checks"].pop()
        self.assertIn("MECHANISM_ROLES",codes(m))
    def test_represented_requires_link(self):
        m=fixture();m["mechanism_checks"][0]["status"]="represented"
        self.assertIn("UNLINKED_REPRESENTED_MECHANISM",codes(m))
    def test_represented_with_real_link_and_source(self):
        m=fixture();m["mechanism_checks"][0].update(
            status="represented",linked_ids=["cash_in"],evidence_refs=[REF])
        self.assertTrue(audit_v2(m,PACKET)["accepted"])
    def test_wrong_link(self):
        m=fixture();m["informational_links"]=[{"from":"cash","to":"missing",
                                              "type":"information","why":"test"}]
        self.assertIn("DANGLING_INFORMATIONAL_LINK",codes(m))
    def test_wrong_initial_source_epistemic(self):
        m=fixture();p=copy.deepcopy(PACKET);p["source_ledger"][0]["kind"]="CALIBRADO"
        self.assertIn("STOCK_SOURCE_LABEL",codes(m,p))
    def test_pipe_source_epistemic(self):
        m=fixture();p=copy.deepcopy(PACKET);p["source_ledger"][0]["kind"]="CALIBRADO"
        self.assertIn("PIPE_SOURCE_LABEL",codes(m,p))
    def test_no_numeric_projections(self):
        m=fixture();m["scenario_projections"]=[{"fake":25}]
        self.assertIn("UNVALIDATED_PROJECTION",codes(m))
    def test_no_delivery_decision_without_model(self):
        m=fixture();m["decision"]["choice"]="open_full"
        self.assertIn("UNSUPPORTED_DECISION",codes(m))
    def test_reject_false_identifiability(self):
        m=fixture();m["identifiability"]["status"]="identifiable"
        self.assertIn("UNSUPPORTED_IDENTIFIABLE",codes(m))
    def test_no_mutation(self):
        m=fixture();saved=copy.deepcopy(m)
        audit_v2(m,PACKET)
        self.assertEqual(m,saved)
if __name__=="__main__":unittest.main()

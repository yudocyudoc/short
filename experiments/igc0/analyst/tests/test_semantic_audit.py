#!/usr/bin/env python3
"""Regression tests for IGC0 posthoc semantic audit; no Cloudflare calls."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from semantic_audit import audit

REF={"source_id":"POS:D01:valle_am","sha256":"a"*64}
PACKET={"source_ledger":[{"source_id":REF["source_id"],"sha256":REF["sha256"],"kind":"OBSERVADO"}],
        "operating_reference":{}}

def base():
    return {"case_id":"M01",
            "stocks":[{"id":"cash","unit":"MXN","initial":100.0,
                       "initial_label":"OBSERVADO","initial_refs":[REF]}],
            "pipes":[{"id":"cash_in","from":"external","to":"cash",
                      "unit_per_time":"MXN/day","mechanism":"ingreso monetario",
                      "evidence_refs":[REF],"epistemic":"OBSERVADO",
                      "capacity_source":None}],
            "contrast":[{"pipe_or_mechanism_id":"cash_in","type":"none",
                         "evidence_refs":[REF],"epistemic":"OBSERVADO",
                         "explanation":"No hay diferencia demostrada en evidencia disponible"}],
            "identifiability":{"status":"insufficient_data",
                               "rival_mechanisms":[],
                               "discriminating_measurement":"traza de cobros"},
            "unknowns":["Falta contraparte contrafactual"]}

class TestSemanticAudit(unittest.TestCase):
    def test_sourced_dimensionally_consistent_graph(self):
        self.assertTrue(audit(base(),PACKET)["accepted"])
    def test_no_contrast_rejects(self):
        m=base();m["contrast"]=[]
        self.assertIn("MISSING_IGC_CONTRAST",[x["code"] for x in audit(m,PACKET)["issues"]])
    def test_stock_initial_without_reference(self):
        m=base();m["stocks"][0]["initial_refs"]=[]
        self.assertIn("UNSUPPORTED_STOCK_INITIAL",[x["code"] for x in audit(m,PACKET)["issues"]])
    def test_calibrated_ref_cannot_be_called_observed(self):
        m=base();p=copy.deepcopy(PACKET);p["source_ledger"][0]["kind"]="CALIBRADO"
        self.assertIn("EPISTEMIC_MISMATCH",[x["code"] for x in audit(m,p)["issues"]])
    def test_pipe_without_observation_ref(self):
        m=base();m["pipes"][0]["evidence_refs"]=[]
        self.assertIn("PIPE_WITHOUT_EVIDENCE",[x["code"] for x in audit(m,PACKET)["issues"]])
    def test_money_not_food_stock_flow(self):
        m=base()
        m["stocks"].append({"id":"inventory","unit":"meals_equivalent","initial":5,
                            "initial_label":"OBSERVADO","initial_refs":[REF]})
        m["pipes"].append({"id":"bad_sales","from":"inventory","to":"cash",
                           "unit_per_time":"meals/day","mechanism":"mezcla incorrecta",
                           "epistemic":"OBSERVADO","evidence_refs":[REF]})
        codes=[x["code"] for x in audit(m,PACKET)["issues"]]
        self.assertIn("CROSS_DOMAIN_STOCK_FLOW",codes)
    def test_wrong_money_unit_to_stock(self):
        m=base();m["pipes"][0]["unit_per_time"]="orders/day"
        self.assertIn("RATE_STOCK_UNIT_MISMATCH",[x["code"] for x in audit(m,PACKET)["issues"]])
    def test_non_identifiable_requires_rivals(self):
        m=base();m["identifiability"]["status"]="non_identifiable"
        self.assertIn("NON_IDENTIFIABILITY_UNSUPPORTED",[x["code"] for x in audit(m,PACKET)["issues"]])
    def test_uncertainty_not_silent(self):
        m=base();m["unknowns"]=[]
        self.assertIn("UNDECLARED_UNCERTAINTY",[x["code"] for x in audit(m,PACKET)["issues"]])
    def test_audit_never_mutates(self):
        m=base();p=copy.deepcopy(PACKET);x=copy.deepcopy(m)
        audit(m,p)
        self.assertEqual(m,x)
if __name__=="__main__":
    unittest.main()

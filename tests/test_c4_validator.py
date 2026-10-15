#!/usr/bin/env python3
"""C4 acceptance and negative controls; these tests never call Workers AI."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from c4_validator import validate_raw, validate_model, load_transport, compact_feedback

FACTS=json.loads((ROOT/"experiments/c4/evaluation/facts.json").read_text())

def gold():
    f=FACTS
    pending=f["requests_total"]-f["rejected_before_acceptance"]-f["canceled_after_acceptance"]-f["prepared_delivered"]
    accepted=f["requests_total"]-f["rejected_before_acceptance"]
    def edge(i,e,src,dst,n,u):
        return {"id":i,"entity":e,"from":src,"to":dst,"total":n,"unit":u}
    return {
      "horizon_hours":f["horizon_hours"],
      "stocks":[
        {"id":"inventory","unit":"beverage_equivalent","initial":f["initial_inventory"],"final":f["initial_inventory"]-f["prepared_delivered"]},
        {"id":"accepted_pending","unit":"request","initial":f["initial_pending"],"final":pending},
      ],
      "flows":[
        edge("request_in","request","external","submitted",f["requests_total"],"request"),
        edge("accept","request","submitted","accepted_pending",accepted,"request"),
        edge("reject","request","submitted","rejected",f["rejected_before_acceptance"],"request"),
        edge("cancel","request","accepted_pending","canceled",f["canceled_after_acceptance"],"request"),
        edge("fulfill","request","accepted_pending","fulfilled",f["prepared_delivered"],"request"),
        edge("use_material","material","inventory","consumed",f["prepared_delivered"],"beverage_equivalent"),
      ],
      "capacity":{"machine_per_hour":f["machine_capacity_per_hour"],"machine_period_max":f["machine_capacity_per_hour"]*f["horizon_hours"],
                  "material_period_max":f["initial_inventory"],"joint_period_max":min(f["initial_inventory"],f["machine_capacity_per_hour"]*f["horizon_hours"]),
                  "observed_prepared":f["prepared_delivered"]},
      "feedback":[],"unknowns":["Tiempo de llegada de las solicitudes"]
    }

class TestC4(unittest.TestCase):
    def invalid(self,change,gate):
        example=gold();change(example);raw=json.dumps(example)
        res=validate_raw(raw,FACTS)
        self.assertEqual(res["status"],"REJECT")
        self.assertIn(gate,[g["id"] for g in res["gates"] if not g["pass"]])
        return res
    def test_gold(self):
        res=validate_raw(json.dumps(gold()),FACTS)
        self.assertEqual(res["status"],"ACCEPT",res)
        self.assertEqual(res["score"],10)
    def test_single_fence_transport(self):
        raw="```json\n"+json.dumps(gold())+"\n```"
        res=validate_raw(raw,FACTS)
        self.assertEqual(res["score"],10)
        self.assertTrue(res["transport"]["stripped_fence"])
    def test_no_prose_extraction(self):
        res=validate_raw("Esta es mi respuesta: "+json.dumps(gold()),FACTS)
        self.assertEqual(res["status"],"REJECT")
        self.assertEqual(res["score"],0)
    def test_broken_json(self):
        self.assertEqual(validate_raw('{"stocks": ',FACTS)["score"],0)
    def test_stock_fictitious(self):
        report=self.invalid(lambda x:x["stocks"].append({"id":"prepared_stock","unit":"beverage","initial":0,"final":0}),"G2_STOCKS")
        # Independence: inventario y pendientes siguen siendo válidos.
        self.assertTrue(next(v["pass"] for v in report["gates"] if v["id"]=="G7_INVENTORY"))
        self.assertTrue(next(v["pass"] for v in report["gates"] if v["id"]=="G6_PENDING"))
    def test_missing_stock(self):
        self.invalid(lambda x:x["stocks"].pop(),"G2_STOCKS")
    def test_duplicate_flow(self):
        self.invalid(lambda x:x["flows"].append(copy.deepcopy(x["flows"][0])),"G3_FLOW_TYPES")
    def test_mismatched_unit(self):
        self.invalid(lambda x:x["flows"][0].update(unit="request/hour"),"G3_FLOW_TYPES")
    def test_reject_after_acceptance(self):
        self.invalid(lambda x:x["flows"][2].update(**{"from":"accepted_pending"}),"G4_TOPOLOGY")
    def test_missing_route(self):
        self.invalid(lambda x:x["flows"].pop(0),"G4_TOPOLOGY")
    def test_wrong_request_total(self):
        self.invalid(lambda x:x["flows"][0].update(total=99),"G5_REQUEST_COUNTS")
    def test_wrong_pending(self):
        self.invalid(lambda x:x["stocks"][1].update(final=0),"G6_PENDING")
    def test_wrong_inventory(self):
        self.invalid(lambda x:x["stocks"][0].update(final=0),"G7_INVENTORY")
    def test_wrong_capacity(self):
        self.invalid(lambda x:x["capacity"].update(joint_period_max=500),"G8_CAPACITY")
    def test_domain_coupling(self):
        self.invalid(lambda x:x["flows"][5].update(total=15),"G9_COUPLING")
    def test_observed_feedback(self):
        self.invalid(lambda x:x["feedback"].append({"name":"Reputación","status":"observed","justification":"imaginado"}),"G10_EPISTEMIC")
    def test_no_unknowns(self):
        self.invalid(lambda x:x.update(unknowns=[]),"G10_EPISTEMIC")
    def test_no_mutation(self):
        o=gold();snap=json.dumps(o,sort_keys=True)
        validate_model(o,FACTS)
        self.assertEqual(json.dumps(o,sort_keys=True),snap)
    def test_error_reasons_do_not_leak_expected_values(self):
        o=gold();o["stocks"][1]["final"]=0
        output=compact_feedback(validate_model(o,FACTS))
        self.assertTrue(any(x["id"]=="G6_PENDING" for x in output))
        self.assertNotIn("8",json.dumps(output,ensure_ascii=False))
    def test_invalid_amount(self):
        self.invalid(lambda x:x["flows"][0].update(total=-1),"G1_SCHEMA")

if __name__=="__main__": unittest.main()

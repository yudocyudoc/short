#!/usr/bin/env python3
"""Tests verify accept and rejection paths; the verifier never repairs a graph."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from c3_validator import validate, load_and_validate

FACTS = json.loads((ROOT / "experiments/c3/evaluation/facts.json").read_text())


def valid_graph():
    f = FACTS
    accepted = f["requests_total"] - f["rejected_before_acceptance"]
    pending = f["initial_pending"] + accepted - f["canceled_after_acceptance"] - f["prepared_delivered"]
    inv_final = f["initial_inventory"] - f["prepared_delivered"]
    horizon = f["horizon_hours"]
    machine_total = horizon * f["machine_capacity_per_hour"]
    def edge(id, entity, origin, dest, qty, unit):
        return {"id": id, "entity": entity, "from": origin, "to": dest, "total": qty, "unit": unit}
    return {
      "horizon_hours": horizon,
      "stocks": [
         {"id":"inventory","unit":"beverage_equivalent","initial":f["initial_inventory"],"final":inv_final},
         {"id":"accepted_pending","unit":"request","initial":f["initial_pending"],"final":pending},
      ],
      "flows": [
         edge("requests", "request", "external", "submitted",f["requests_total"],"request"),
         edge("accept", "request", "submitted", "accepted_pending",accepted,"request"),
         edge("reject", "request", "submitted", "rejected",f["rejected_before_acceptance"],"request"),
         edge("cancel", "request", "accepted_pending", "canceled",f["canceled_after_acceptance"],"request"),
         edge("fulfill", "request", "accepted_pending", "fulfilled",f["prepared_delivered"],"request"),
         edge("material_use", "material", "inventory", "consumed",f["prepared_delivered"],"beverage_equivalent"),
      ],
      "capacity":{
         "machine_per_hour": f["machine_capacity_per_hour"],
         "machine_period_max": machine_total,
         "material_period_max": f["initial_inventory"],
         "joint_period_max": min(machine_total, f["initial_inventory"]),
         "observed_prepared": f["prepared_delivered"],
      },
      "feedback": [],
      "unknowns": ["No se conoce la distribución temporal de solicitudes."],
    }


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.gold = valid_graph()
    def outcome(self, mutate=None):
        item = copy.deepcopy(self.gold)
        if mutate is not None:
            mutate(item)
        return validate(item, FACTS)
    def failed(self, result, gate):
        self.assertEqual(result["status"],"REJECT")
        self.assertIn(gate, [x["id"] for x in result["gates"] if not x["pass"]])
    def test_gold_is_accepted(self):
        report = self.outcome()
        self.assertEqual(report["status"],"ACCEPT",str(report))
        self.assertEqual(report["score"],10)
    def test_missing_json_is_rejected(self):
        self.failed(load_and_validate("Here is: "+json.dumps(self.gold), FACTS),"G1_JSON")
    def test_extra_stock_is_rejected(self):
        self.failed(self.outcome(lambda x:x["stocks"].append(
            {"id":"prepared_stock","unit":"beverage","initial":0,"final":0})),"G2_STOCKS")
    def test_duplicate_flow_is_rejected(self):
        self.failed(self.outcome(lambda x:x["flows"].append(copy.deepcopy(x["flows"][0]))),"G3_FLOW_TYPES")
    def test_rate_unit_is_rejected(self):
        self.failed(self.outcome(lambda x:x["flows"][0].update(unit="request/hour")),"G3_FLOW_TYPES")
    def test_reject_after_acceptance_is_rejected(self):
        self.failed(self.outcome(lambda x:x["flows"][2].update(**{"from":"accepted_pending"})),"G4_REQUEST_PATHS")
    def test_lost_request_is_rejected(self):
        self.failed(self.outcome(lambda x:x["flows"][0].update(total=32)),"G5_REQUEST_TOTALS")
    def test_wrong_pending_is_rejected(self):
        self.failed(self.outcome(lambda x:x["stocks"][1].update(final=3)),"G6_PENDING_BALANCE")
    def test_wrong_inventory_is_rejected(self):
        self.failed(self.outcome(lambda x:x["stocks"][0].update(final=0)),"G7_MATERIAL_BALANCE")
    def test_capacity_wrong_is_rejected(self):
        self.failed(self.outcome(lambda x:x["capacity"].update(machine_period_max=99)),"G8_CAPACITY")
    def test_material_not_coupled_to_delivery(self):
        self.failed(self.outcome(lambda x:x["flows"][5].update(total=14)),"G9_CROSS_DOMAIN")
    def test_observed_feedback_is_rejected(self):
        self.failed(self.outcome(lambda x:x["feedback"].append({
            "name":"Reputacion", "status":"observed", "justification":"Hipótesis no observada"})),"G10_EPISTEMIC")
    def test_missing_uncertainty_is_rejected(self):
        self.failed(self.outcome(lambda x:x.update(unknowns=[])),"G10_EPISTEMIC")
    def test_negative_flow_rejected_as_schema(self):
        self.failed(self.outcome(lambda x:x["flows"][0].update(total=-1)),"G1_JSON")
    def test_no_silent_repair(self):
        candidate = copy.deepcopy(self.gold)
        candidate["stocks"][0]["final"] = 0
        before = json.dumps(candidate,sort_keys=True)
        result = validate(candidate, FACTS)
        self.assertEqual(json.dumps(candidate,sort_keys=True),before)
        self.assertEqual(result["status"],"REJECT")


if __name__=="__main__":
    unittest.main()

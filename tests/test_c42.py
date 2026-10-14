#!/usr/bin/env python3
"""C4.2 tests — transport and independently accountable stocks, no AI calls."""
import copy
import json
import sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from test_c4_validator import gold
from c42_transport import separate
from c42_validator import evaluate,check_stock_flow_coverage

FACTS=json.loads((ROOT/"experiments"/"c4"/"evaluation"/"facts.json").read_text())
GOOD=gold()

class TestC42Transport(unittest.TestCase):
    def test_pure_json(self):
        obj,think,m=separate(json.dumps(GOOD))
        self.assertEqual(obj,GOOD);self.assertIsNone(think);self.assertTrue(m["ok"])
    def test_single_fence(self):
        obj,think,m=separate("```json\n"+json.dumps(GOOD)+"\n```")
        self.assertEqual(obj,GOOD);self.assertTrue(m["had_fence"])
    def test_balanced_thinking_and_fence(self):
        raw="<think>Razono sin exponerlo como JSON.</think>\n```json\n"+json.dumps(GOOD)+"\n```"
        obj,think,m=separate(raw)
        self.assertEqual(obj,GOOD);self.assertTrue(m["had_think"])
        self.assertEqual(think,"Razono sin exponerlo como JSON.")
    def test_balanced_thinking_and_pure_json(self):
        obj,think,m=separate("<think>x</think>\n"+json.dumps(GOOD))
        self.assertEqual(obj,GOOD);self.assertTrue(m["ok"])
    def test_native_provider_object(self):
        obj,think,m=separate(GOOD)
        self.assertEqual(obj,GOOD);self.assertEqual(m["format"],"provider_object")
    def test_missing_close(self):
        self.assertFalse(separate("<think>reason\n"+json.dumps(GOOD))[2]["ok"])
    def test_unexpected_close(self):
        self.assertFalse(separate("</think>"+json.dumps(GOOD))[2]["ok"])
    def test_two_think_segments(self):
        self.assertFalse(separate("<think>a</think><think>b</think>"+json.dumps(GOOD))[2]["ok"])
    def test_extra_prose(self):
        self.assertFalse(separate("Este es: "+json.dumps(GOOD))[2]["ok"])
        self.assertFalse(separate(json.dumps(GOOD)+" FIN")[2]["ok"])
    def test_nested_fences(self):
        x="```json\n```json\n"+json.dumps(GOOD)+"\n```\n```"
        self.assertFalse(separate(x)[2]["ok"])
    def test_truncated(self):
        self.assertFalse(separate('{"stocks": ')[2]["ok"])
    def test_array_not_model_object(self):
        self.assertFalse(separate("[]")[2]["ok"])

class TestC42Ledger(unittest.TestCase):
    def test_gold_accepted(self):
        v=evaluate(GOOD,FACTS)
        self.assertEqual(v["status"],"ACCEPT")
        self.assertEqual(v["c4_score"],10)
        self.assertTrue(v["p11_pass"])
        self.assertEqual(len(v["p11"]["certificates"]),2)
    def test_missing_material_even_if_final_stock_correct(self):
        x=copy.deepcopy(GOOD)
        x["flows"]=[f for f in x["flows"] if f["entity"]!="material"]
        v=evaluate(x,FACTS)
        self.assertFalse(v["p11_pass"])
        by={a["stock"]:a for a in v["p11"]["certificates"]}
        self.assertFalse(by["inventory"]["pass"])
        self.assertEqual(by["inventory"]["declared_delta"],-21)
        self.assertEqual(by["inventory"]["flow_delta"],0)
    def test_missing_request_flow(self):
        x=copy.deepcopy(GOOD)
        x["flows"]=[f for f in x["flows"] if f["to"]!="fulfilled"]
        v=evaluate(x,FACTS)
        by={a["stock"]:a for a in v["p11"]["certificates"]}
        self.assertFalse(by["accepted_pending"]["pass"])
    def test_incompatible_unit_material(self):
        x=copy.deepcopy(GOOD)
        x["flows"][-1]["unit"]="request"
        self.assertFalse(evaluate(x,FACTS)["p11_pass"])
    def test_wrong_delta_material(self):
        x=copy.deepcopy(GOOD)
        x["stocks"][0]["final"]=30
        self.assertFalse(evaluate(x,FACTS)["p11_pass"])
    def test_fake_ready_stock_rejected_by_C4(self):
        x=copy.deepcopy(GOOD)
        x["stocks"].append({"id":"prepared_stock","unit":"beverage","initial":0,"final":0})
        v=evaluate(x,FACTS)
        self.assertEqual(v["status"],"REJECT")
        self.assertFalse(any(g["pass"] for g in v["c4_gates"] if g["id"]=="G2_STOCKS"))
    def test_no_mutation_or_autorepair(self):
        x=copy.deepcopy(GOOD);x["flows"].pop()
        before=json.dumps(x,sort_keys=True)
        evaluate(x,FACTS)
        self.assertEqual(json.dumps(x,sort_keys=True),before)
    def test_invalid_json_evaluation(self):
        v=evaluate(None,FACTS)
        self.assertEqual(v["status"],"FORMAT_REJECT")
        self.assertFalse(v["p11_pass"])

if __name__=="__main__":unittest.main()

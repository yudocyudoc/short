"""Offline contract tests for the Short-hosted NW2 inference diagnostic."""
from pathlib import Path
import json
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[2]
run = runpy.run_path(str(ROOT / "experiments/igc-glm53-nw2/run_probe.py"))
validate_request = run["validate_request"]
parse_selection = run["parse_selection"]

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.good = {
            "selected_candidate_ids": ["urn:igc:candidate:CS-01"],
            "rationale": "Some structures remain plausible.",
            "falsifier": "Collect a fresh dense transient.",
            "unknowns": ["Measurement noise"],
            "next_test": "New pulse with early samples."
        }

    def test_igc_frozen_request_system_user(self):
        path = ROOT / "experiments/igc-glm53-nw2/request.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        body = validate_request(doc)
        self.assertEqual([x["role"] for x in body["messages"]], ["system", "user"])
        self.assertEqual(body["temperature"], 0)
        self.assertEqual(body["max_completion_tokens"], 4096)
        self.assertEqual(body["reasoning_effort"], "low")

    def test_complete_json(self):
        self.assertEqual(parse_selection(json.dumps(self.good)), self.good)

    def test_fenced_json(self):
        self.assertEqual(parse_selection("```json\n" + json.dumps(self.good) + "\n```"), self.good)

    def test_abstention_allowed(self):
        obj = dict(self.good, selected_candidate_ids=[])
        self.assertEqual(parse_selection(json.dumps(obj))["selected_candidate_ids"], [])

    def test_invalid_and_unknown_candidate_rejected(self):
        for payload in ("", "not json", "{", json.dumps(dict(self.good, selected_candidate_ids=["CS-03"]))):
            with self.subTest(payload=payload[:12]), self.assertRaises(ValueError):
                parse_selection(payload)

if __name__ == "__main__":
    unittest.main()

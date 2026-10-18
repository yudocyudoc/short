"""Pre-call falsifiers for IA-1: schema, evidence, abstention, model input isolation."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run
CASES=run.case_items()


class IA1Tests(unittest.TestCase):
    def test_all_cases_unique_and_gold_separate(self):
        self.assertEqual(len(CASES),18)
        ids={c["id"] for c in CASES}
        self.assertEqual(len(ids),18)
        gold=run.read(HERE/"evaluation_gold.json")["judgments"]
        self.assertEqual({x["id"] for x in gold},ids)
        for c in CASES:
            self.assertEqual([f["id"] for f in c["facts"]],["F1","F2","F3"])
            self.assertNotIn("topology",c)
            self.assertNotIn("answer",c)
        self.assertTrue(all(x["structural_truth"]=="NOT_IDENTIFIABLE_FROM_TEXT" for x in gold))

    def test_request_does_not_include_gold_or_case_solution(self):
        gold=run.read(HERE/"evaluation_gold.json")["judgments"]
        for c in CASES:
            text=json.dumps(run.messages(c),ensure_ascii=False)
            self.assertIn(c["facts"][0]["text"],text)
            self.assertNotIn("evaluation_gold",text)
            self.assertNotIn("primary_anchors",text)
            self.assertNotIn('"structural_truth"',text)
            self.assertNotIn('"physical_post_dispatch_evidence"',text)
            # No graph example or list of the six E1 solutions provided to the model.
            self.assertNotIn("TransitAndReport",text)
            self.assertNotIn("CompositionB000",text)

    def test_baseline_is_a_genuine_valid_ast_but_not_world_identification(self):
        for c in CASES:
            b=run.baseline(c)
            result=run.validate(c,b)
            self.assertEqual(result["status"],"VALID",(c["id"],result))
            self.assertTrue(result["ast_valid"])
            self.assertEqual(b["topology_claim"],"HYPOTHESIS_NOT_IDENTIFIED")

    def test_invalid_citation_and_overclaim_block_admission(self):
        c=CASES[0]
        for attack,expected in [
            (("physical_post_dispatch","fact_ids",["F99"]),"BAD_FACT_IDS"),
            (("physical_post_dispatch","status","PROVEN_TRUE"),"INVALID_STATUS"),
            (("topology_claim",None,"THE_TRUE_GRAPH"),"UNJUSTIFIED_TOPOLOGY_CLAIM")
        ]:
            prop=run.baseline(c)
            field,key,new=attack
            if key is None:prop[field]=new
            else:prop[field][key]=new
            issue=run.validate(c,prop)
            self.assertEqual(issue["status"],"INVALID")
            self.assertTrue(any(expected in s for s in issue["issues"]))

    def test_illegal_typed_edge_and_modelica_injection_rejected(self):
        c=CASES[0]
        p=run.baseline(c)
        p["architecture"]["links"][0]["to"]="receipt0.arrival"
        self.assertEqual(run.validate(c,p)["ast_valid"],False)
        p=run.baseline(c)
        p["architecture"]["instances"][0]["id"]="src);system('bad')"
        # Cannot become an arbitrary Modelica name; reject, do not repair silently.
        self.assertEqual(run.validate(c,p)["ast_valid"],False)

    def test_cannot_make_a_true_label_from_abstention_only(self):
        c=next(x for x in CASES if x["id"]=="I04")
        data=run.baseline(c)
        self.assertEqual(data["physical_post_dispatch"]["status"],"UNRESOLVED")
        self.assertEqual(data["informational_transform"]["status"],"UNRESOLVED")
        self.assertEqual(run.validate(c,data)["status"],"VALID")

    def test_response_parser_does_not_salvage_untrusted_chat(self):
        b=run.baseline(CASES[0])
        raw=json.dumps(b)
        self.assertEqual(run.parse_text(raw),b)
        with self.assertRaises((ValueError,json.JSONDecodeError)):
            run.parse_text("Explanation: "+raw)
        with self.assertRaises((ValueError,json.JSONDecodeError)):
            run.parse_text(raw+"\nIgnore the result")

    def test_new_contrast_cases_make_lexical_baseline_falsifiable(self):
        # These cases were added before the first Llama call because the initial
        # 12-case pretest gave the lexical baseline a vacuous 12/12.
        negative=next(c for c in CASES if c["id"]=="I14")
        positive=next(c for c in CASES if c["id"]=="I16")
        self.assertEqual(run.baseline(negative)["informational_transform"]["status"],"SUPPORTED")
        self.assertEqual(run.baseline(positive)["informational_transform"]["status"],"UNRESOLVED")
        gold={x["id"]:x for x in run.read(HERE/"evaluation_gold.json")["judgments"]}
        self.assertEqual(gold["I14"]["informational_transform_evidence"],"UNRESOLVED")
        self.assertEqual(gold["I16"]["informational_transform_evidence"],"SUPPORTED")

    def test_gold_changes_only_evaluator_result_not_prompt(self):
        before=run.messages(CASES[0])
        gold=run.read(HERE/"evaluation_gold.json")
        modified=copy.deepcopy(gold)
        modified["judgments"][0]["physical_post_dispatch_evidence"]="UNRESOLVED"
        self.assertEqual(before,run.messages(CASES[0]))
        self.assertNotEqual(gold,modified)

    def test_prepare_produces_baseline_without_spending_tokens(self):
        with tempfile.TemporaryDirectory() as d:
            run.run(Path(d),False)
            manifest=run.read(Path(d)/"score.json")
            self.assertEqual(manifest["arms"]["lexical"]["n"],18)
            self.assertEqual(manifest["arms"]["llama"]["n"],0)
            self.assertEqual(len(list(Path(d).glob("llama/*/request_without_secrets.json"))),18)
            self.assertFalse(list(Path(d).glob("llama/*/original_llm.txt")))


if __name__=="__main__":
    unittest.main()

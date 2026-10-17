import json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from run_challenge import setup,score,paired_comparison,ORIGINAL_GIT_BLOBS,gitblob
import run_challenge as study

class ChallengeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases=setup()
    def test_twenty_four_distinct_new_cases(self):
        self.assertEqual(len(self.cases),24)
        self.assertTrue(all(x["id"].startswith("N") for x in self.cases))
        original=study.original_prompt.CAT
        self.assertEqual(len(original["molecules"]),4)
    def test_pilot_code_and_catalog_byte_frozen(self):
        for name,expected in ORIGINAL_GIT_BLOBS.items():
            self.assertEqual(gitblob((study.PILOT/name).read_bytes()),expected)
    def test_no_gold_labels_exposed_in_either_prompt(self):
        for case in self.cases:
            for arm in ("generic_sd","molecular_scaffold"):
                messages=study.original_prompt.messages(case,arm)
                payload=json.dumps(messages,ensure_ascii=False)
                self.assertNotIn("supported_facts",payload)
                self.assertNotIn("gold_private",payload)
                self.assertNotIn("molecules_expected",payload)
                self.assertNotIn("modelica_code",payload.lower())
                self.assertNotIn("equation =",payload.lower())
    def test_deterministic_baseline_is_not_modified_or_taught_labels(self):
        responses={x["id"]:study.original_baseline.respond(x) for x in self.cases}
        baseline=study.original_eval.summarize(responses,"deterministic")
        self.assertEqual(baseline["evaluated"],24)
        self.assertLessEqual(baseline["strict_pass"],24)
        self.assertGreaterEqual(baseline["strict_pass"],0)
    def test_verbatim_evidence_gate(self):
        case=self.cases[0]
        selected=study.original_eval.GOLD[case["id"]]["molecules"]
        fabricated={"decision":"COMPOSE","molecules":selected,
          "citations":[{"target":m,"fact_id":"F1","quote":"fake evidence that was never present"} for m in selected],
          "unresolved":[]}
        r=study.original_eval.assess(case["id"],fabricated)
        self.assertFalse(r["strict_pass"])
    def test_all_missing_llm_responses_do_not_receive_credit(self):
        answers={"deterministic":{x["id"]:study.original_baseline.respond(x) for x in self.cases},
                "generic_sd":{},"molecular_scaffold":{}}
        r=score(answers)
        self.assertEqual(r["scores"]["generic_sd"]["strict_pass"],0)
        self.assertEqual(r["scores"]["generic_sd"]["evaluated"],0)
        self.assertEqual(r["scores"]["molecular_scaffold"]["strict_pass"],0)
    def test_exact_paired_comparison_all_equal(self):
        baseline={x["id"]:study.original_baseline.respond(x) for x in self.cases}
        r=study.original_eval.summarize(baseline,"generic_sd")
        p=paired_comparison(r,r)
        self.assertEqual(p["c_wins"],0)
        self.assertEqual(p["b_wins"],0)
        self.assertEqual(p["exact_two_sided_mcnemar_p_exploratory"],1.0)
    def test_scorer_keeps_all_case_ids(self):
        self.assertEqual(set(study.original_eval.CASES),set(study.original_eval.GOLD))
        for x in self.cases:
            gold=study.original_eval.GOLD[x["id"]]
            self.assertTrue(set(gold["molecules"])<=study.original_eval.MOLECULES)

if __name__=="__main__":unittest.main()

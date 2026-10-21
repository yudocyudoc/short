"""No-cost EPI-02 test suite; all cases and gold frozen before any inference."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

prep=load("epi02_prep",HERE/"prepare.py")
ev=load("epi02_eval",HERE/"evaluate.py")
runmod=load("epi02_runner",HERE/"scripts"/"run_cloudflare.py")
CASES=json.loads((HERE/"cases.json").read_text(encoding="utf-8"))["cases"]
GOLD=json.loads((HERE/"evaluation/gold.json").read_text(encoding="utf-8"))["cases"]

class ExperimentTests(unittest.TestCase):
    def test_exact_pinned_igc_blob(self):
        b=(HERE/"references"/"f0_atms_probe.py").read_bytes()
        actual=hashlib.sha1(("blob "+str(len(b))+"\0").encode()+b).hexdigest()
        self.assertEqual(actual,prep.PROBE_BLOB)

    def test_gold_frozen_for_all_revisions_and_unseen_counterfactual(self):
        self.assertEqual(len(CASES),2)
        for case in CASES:
            self.assertTrue(case["id"].startswith("EPI02-"))
            gold=GOLD[case["id"]]
            for revision in case["revisions"]:
                actual=prep.status(prep.calculate(case,revision["invalidated"]))
                self.assertEqual(actual,gold[revision["id"]])
            extra=case["revisions"][-1]["invalidated"]+case["counterfactual"]["additional_invalidated"]
            self.assertEqual(prep.status(prep.calculate(case,extra)),gold["CF"])

    def test_equal_evidence_b_c_but_no_counterfactual_answers_leak(self):
        for case in CASES:
            b,c=prep.build(case)["B"],prep.build(case)["C"]
            self.assertEqual(b["dossier"],c["dossier"])
            self.assertEqual(b["status_by_revision"],c["status_by_revision"])
            self.assertNotIn("minimal_support_by_revision",b)
            self.assertIn("minimal_support_by_revision",c)
            self.assertNotIn("CF",c["minimal_support_by_revision"])
            self.assertNotIn("CF",b["status_by_revision"])
            self.assertIn("additional_invalidated",c["dossier"]["counterfactual"])

    def test_prepared_with_no_calls_and_no_evaluator_content(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)
            report=prep.prepare(out)
            self.assertEqual(report["calls_made"],0)
            self.assertEqual(report["calls_planned"],24)
            self.assertEqual(len(list(out.glob("context-*.json"))),4)
            for file in out.glob("context-*.json"):
                text=file.read_text(encoding="utf-8")
                self.assertNotIn("historical_note",text)
                self.assertNotIn("evaluator_only",text)

    def test_pure_json_fence_and_foreign_identifier_have_separate_flags(self):
        raw=json.dumps({"case_id":CASES[0]["id"],"task_id":"COUNTERFACTUAL",
             "hypothesis_states":[{"hypothesis_id":"bogus|id","revision":"CF","status":"SUPPORTED"}],
             "justification_assessment":[],"explanation":"","uncertainties":[]})
        parsed,fmt,issues=ev.parse(raw)
        self.assertEqual((fmt,issues),("PURE_JSON",[]))
        grade=ev.validate_answer(parsed,CASES[0],"COUNTERFACTUAL",GOLD[CASES[0]["id"]])
        self.assertTrue(any(x.startswith("INVALID_HYPOTHESIS_ID") for x in grade["issues"]))
        fenced=chr(96)*3+"json\n"+raw+"\n"+chr(96)*3
        parsed,fmt,issues=ev.parse(fenced)
        self.assertEqual(fmt,"FENCES_REMOVED")
        self.assertIn("NON_PURE_JSON_FENCES",issues)
        self.assertEqual(parsed["case_id"],CASES[0]["id"])

    def test_internal_contradiction_is_flagged_not_repaired(self):
        case=CASES[1]
        hid=case["hypotheses"][0]["id"]
        j=next(x for x in case["rules"] if x["consequent"]==hid)
        x={"case_id":case["id"],"task_id":"COUNTERFACTUAL",
           "hypothesis_states":[{"hypothesis_id":hid,"revision":"CF","status":"UNSUPPORTED"}],
           "justification_assessment":[{"justification_id":j["id"],"status":"ACTIVE",
                        "evidence_refs":j["source_ids"],"assumption_refs":[]}],
           "explanation":"","uncertainties":[]}
        grade=ev.validate_answer(x,case,"COUNTERFACTUAL",GOLD[case["id"]])
        self.assertIn("INTERNAL_CONTRADICTION_ACTIVE_SUPPORT:"+j["id"],grade["issues"])
        self.assertEqual(x["hypothesis_states"][0]["status"],"UNSUPPORTED")

    def test_twelve_schedules_per_arm_max24_and_no_unauthorized_network(self):
        slots=runmod.schedule(CASES)
        self.assertEqual(len(slots),24)
        self.assertEqual(sum(arm=="B" for _,arm,_,_ in slots),12)
        self.assertEqual(sum(arm=="C" for _,arm,_,_ in slots),12)
        called=[]
        def send(*args,**kwargs):
            called.append(True)
            raise AssertionError("network access forbidden")
        with self.assertRaises(SystemExit):
            runmod.run(env={"CLOUDFLARE_ACCOUNT_ID":"fake","CLOUDFLARE_API_TOKEN":"fake"},
                       sender=send)
        self.assertEqual(called,[])
        self.assertEqual(runmod.AUTH,"RUN_EPI02_MAX24")
        self.assertEqual(runmod.MAX_CALLS,24)

if __name__=="__main__":
    unittest.main()

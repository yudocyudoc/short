"""EPI-05 tests: all offline. Mock mode never accesses Cloudflare."""
from __future__ import annotations
import io,json,sys,tempfile,unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import oracle,prepare,evaluate,run_cloudflare

class Diagnostics(unittest.TestCase):
    def test_independent_oracles_and_frozen_gold(self):
        cases,gold=oracle.validate()
        self.assertEqual(len(cases),8)
        self.assertEqual(Counter(gold["statuses"].values()),
          {"NEITHER":5,"BOTH":1,"ONLY_H1":1,"ONLY_H2":1})
        for c in cases:
            self.assertEqual(oracle.enumerate_support(c),oracle.antichain_support(c))

    def test_original_string_and_structured_object_equivalence(self):
        cases,_=oracle.validate()
        for c in cases:
            orig=prepare.build(c,"BASE_STRING_CHOICE")["state"]
            structured=prepare.build(c,"OBJECT_CHOICE")["state"]
            self.assertIsInstance(orig,str)
            self.assertIsInstance(structured,dict)
            self.assertEqual(json.loads(orig),structured)
            baseq=prepare.build(c,"BASE_STRING_CHOICE")["questions"]
            objq=prepare.build(c,"OBJECT_CHOICE")["questions"]
            self.assertEqual(baseq,objq)

    def test_reversal_not_destroyed_by_serialization(self):
        cases,_=oracle.validate()
        for c in cases:
            baseline=prepare.build(c,"BASE_STRING_CHOICE")
            reverse=prepare.build(c,"REVERSED_OPTIONS_CHOICE")
            bo=list(baseline["questions"]["status"]["criteria"])
            ro=list(reverse["questions"]["status"]["criteria"])
            self.assertEqual(ro,list(reversed(bo)))
            self.assertNotEqual(prepare.transport(baseline),prepare.transport(reverse))
            self.assertEqual(baseline["state"],reverse["state"])
            self.assertEqual(set(bo),set(ro))

    def test_explicit_active_is_primitive_not_hypothesis_gold(self):
        cases,_=oracle.validate()
        for c in cases:
            state=json.loads(prepare.build(c,"EXPLICIT_ACTIVE_CHOICE")["state"])
            allowed=set(a["id"] for a in c["assumptions"])-set(c["revisions"][-1]["revoked"])
            self.assertEqual(state["active_assumptions"],sorted(allowed))
            self.assertNotIn("gold",state)
            self.assertNotIn("supported_hypotheses",state)
            self.assertNotIn("support_environments",state)

    def test_typed_binary_questions_are_separate(self):
        cases,_=oracle.validate()
        for c in cases:
            for condition in ("BASE_STRING_BINARY","OBJECT_BINARY"):
                body=prepare.build(c,condition)
                self.assertEqual(set(body["questions"]),{"h1_supported","h2_supported"})
                self.assertTrue(all(x["type"]=="noul" for x in body["questions"].values()))

    def test_schedule_exactly_48_and_no_credentials(self):
        requests=prepare.build_schedule()
        self.assertEqual(len(requests),48)
        self.assertEqual(Counter(r["condition"] for r in requests),
            dict.fromkeys(prepare.CONDITIONS,8))
        self.assertEqual(len({r["sequence"] for r in requests}),48)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);report=prepare.prepare(p)
            self.assertEqual(report["calls_made"],0)
            self.assertEqual(report["calls_planned"],48)
            self.assertEqual(prepare.sha((p/"requests.jsonl").read_bytes()),report["requests_sha256"])
            self.assertFalse((p/"inference-manifest.json").exists())

    def test_no_network_without_separate_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def forbidden(*args,**kwargs):
                calls.append(True)
                raise AssertionError("External network use forbidden")
            with self.assertRaises(SystemExit):
                run_cloudflare.run(Path(d),env={"CLOUDFLARE_ACCOUNT_ID":"test","CLOUDFLARE_API_TOKEN":"test"},sender=forbidden)
            self.assertEqual(calls,[])

    def test_eval_validation_and_binary_metric_distinction(self):
        x,prob,issues=evaluate.evaluate_response({"answers":{"status":{"choice":"NEITHER",
            "probabilities":{"BOTH":.1,"NEITHER":.7,"ONLY_H1":.1,"ONLY_H2":.1}}}},"BASE_STRING_CHOICE")
        self.assertEqual((x,issues),("NEITHER",[]))
        self.assertAlmostEqual(evaluate.brier(x,prob,"NEITHER"),0.12)
        binary={"answers":{"h1_supported":{"type":"noul","noul":.1},
                  "h2_supported":{"type":"noul","noul":.2}}}
        x,prob,issues=evaluate.evaluate_response(binary,"OBJECT_BINARY")
        self.assertEqual((x,issues),("NEITHER",[]))
        self.assertAlmostEqual(evaluate.brier(x,prob,"NEITHER"),.025)
        self.assertNotEqual(set(prob),set(oracle.STATES))

    def test_48_mock_inferences_and_evaluation(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            prepare.prepare(out)
            cases,gold=oracle.validate()
            prepared={prepare.sha(prepare.transport(x["body"]).encode()):x for x in prepare.build_schedule()}
            observed=[]
            def responder(request,timeout):
                body=json.loads(request.data.decode("utf-8"))
                spec=prepared[prepare.sha(prepare.transport(body).encode())]
                observed.append(spec)
                truth=gold["statuses"][spec["id"]]
                if spec["condition"].endswith("BINARY"):
                    a={"h1_supported":{"type":"noul","noul":.9 if truth in ("BOTH","ONLY_H1") else .1},
                       "h2_supported":{"type":"noul","noul":.9 if truth in ("BOTH","ONLY_H2") else .1}}
                else:
                    p={s:.05 for s in oracle.STATES};p[truth]=.85
                    a={"status":{"type":"choice","choice":truth,"probabilities":p,"confidence":.7}}
                raw={"success":True,"result":{"model":"clef","answers":a,"usage":{"input_tokens":300,"output_tokens":0}}}
                return io.BytesIO(json.dumps(raw).encode())
            result=run_cloudflare.run(out,env={
                "EPI05_AUTHORIZATION":"RUN_EPI05_MAX48",
                "CLOUDFLARE_ACCOUNT_ID":"f"*32,"CLOUDFLARE_API_TOKEN":"MOCK_TOKEN"},sender=responder)
            self.assertEqual(result["status"],"COMPLETE")
            self.assertEqual(result["calls_succeeded"],48)
            self.assertEqual(len(observed),48)
            report=evaluate.evaluate(out)
            self.assertEqual(len(report["records"]),48)
            for group in report["by_condition"].values():
                self.assertEqual(group["correct"],8)
                self.assertEqual(group["neither_correct"],5)
                self.assertEqual(group["positive_controls_correct"],3)
                self.assertEqual(group["false_support_count"],0)
            self.assertTrue((out/"evaluation-report.json").exists())

if __name__=="__main__":
    unittest.main()

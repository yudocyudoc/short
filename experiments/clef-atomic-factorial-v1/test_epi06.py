"""EPI-06 2x2 factorial: offline tests only, end-to-end mocked 80 calls."""
from __future__ import annotations
import io,json,sys,tempfile,unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import oracle,prepare,evaluate,run_cloudflare

class Epi06Tests(unittest.TestCase):
    def test_fresh_20_cases_and_double_oracle(self):
        cases,gold=oracle.validate()
        self.assertEqual(len(cases),20)
        self.assertEqual(Counter(gold["case_class"].values()),
          {"BOTH":4,"ONLY_H1":4,"ONLY_H2":4,"NEITHER":8})
        self.assertTrue(all(c["id"].startswith("NX-") for c in cases))
        self.assertTrue(all(c["id"] not in ("HET-08","HET-12") for c in cases))
        for case in cases:
            self.assertEqual(oracle.enumerate_support(case),oracle.antichain_support(case))

    def test_two_distinct_neither_variants_per_graph_family(self):
        cases,gold=oracle.validate()
        scenes={c["scenario"] for c in cases}
        self.assertEqual(len(scenes),4)
        for scene in scenes:
            subset=[c for c in cases if c["scenario"]==scene]
            self.assertEqual(len(subset),5)
            self.assertEqual(sum(gold["case_class"][c["id"]]=="NEITHER" for c in subset),2)
            self.assertEqual(len({tuple(sorted(c["revisions"][-1]["revoked"])) for c in subset}),5)

    def test_all_conditions_have_identical_factual_state(self):
        cases,_=oracle.validate()
        for c in cases:
            state=[prepare.build(c,x)["state"] for x in prepare.CONDITIONS]
            self.assertEqual(len(set(state)),1)
            self.assertNotIn("gold",state[0])
            self.assertNotIn("case_class",state[0])

    def test_instruction_factor_has_exact_shared_insertion(self):
        cases,_=oracle.validate()
        for case in cases:
            for kind in ("CHOICE","BINARY"):
                a=prepare.build(case,kind+"_BASE")
                b=prepare.build(case,kind+"_EXPLICIT")
                qa=a["questions"];qb=b["questions"]
                self.assertEqual(set(qa),set(qb))
                for key in qa:
                    first=qa[key]["instructions"]
                    second=qb[key]["instructions"]
                    self.assertTrue(first.startswith(prepare.CONTEXT))
                    self.assertTrue(second.startswith(prepare.CONTEXT))
                    self.assertNotIn(prepare.STRONG,first)
                    self.assertIn(prepare.STRONG,second)
                    self.assertEqual(first.replace(prepare.CONTEXT,"",1),
                        second.replace(prepare.CONTEXT+" "+prepare.STRONG,"",1))
                    if "criteria" in qa[key]:self.assertEqual(qa[key]["criteria"],qb[key]["criteria"])

    def test_task_factor_preserves_same_common_context_and_option_mapping(self):
        cases,_=oracle.validate()
        for c in cases:
            for level in ("BASE","EXPLICIT"):
                q1=prepare.build(c,"CHOICE_"+level)["questions"]
                q2=prepare.build(c,"BINARY_"+level)["questions"]
                self.assertEqual(q1["status"]["type"],"choice")
                self.assertEqual(list(q1["status"]["criteria"]),list(prepare.CRITERIA))
                self.assertEqual(set(q2),{"h1_supported","h2_supported"})
                self.assertTrue(all(q2[k]["type"]=="noul" for k in q2))
                self.assertIn(prepare.CONTEXT,q1["status"]["instructions"])
                self.assertTrue(all(prepare.CONTEXT in v["instructions"] for v in q2.values()))

    def test_80_requests_with_frozen_no_network_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            pre=prepare.prepare(out)
            self.assertEqual((pre["calls_planned"],pre["inference_calls"]),(80,0))
            reqs=[json.loads(x) for x in (out/"requests.jsonl").read_text().splitlines()]
            self.assertEqual(Counter(x["condition"] for x in reqs),dict.fromkeys(prepare.CONDITIONS,20))
            self.assertEqual(len(set(x["id"] for x in reqs)),20)
            self.assertEqual(pre["requests_sha256"],prepare.sha((out/"requests.jsonl").read_bytes()))
            self.assertFalse((out/"inference-manifest.json").exists())

    def test_explicit_permission_required_for_any_call(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def forbidden(*args,**kwargs):
                calls.append(True);raise AssertionError("Network forbidden")
            with self.assertRaises(SystemExit):
                run_cloudflare.run(Path(d),env={"CLOUDFLARE_ACCOUNT_ID":"x","CLOUDFLARE_API_TOKEN":"x"},sender=forbidden)
            self.assertFalse(calls)

    def test_binary_and_multiclass_metrics_separated(self):
        p={"BOTH":.1,"NEITHER":.7,"ONLY_H1":.1,"ONLY_H2":.1}
        label,probs,errors=evaluate.decode({"answers":{"status":{"choice":"NEITHER","probabilities":p}}},"CHOICE_BASE")
        self.assertEqual((label,errors),("NEITHER",[]))
        self.assertAlmostEqual(evaluate.brier(probs,"NEITHER"),.12)
        obj={"answers":{"h1_supported":{"noul":.1},"h2_supported":{"noul":.2}}}
        label,probs,errors=evaluate.decode(obj,"BINARY_BASE")
        self.assertEqual((label,errors),("NEITHER",[]))
        self.assertAlmostEqual(evaluate.brier(probs,"NEITHER"),.025)
        self.assertNotEqual(set(probs),set(oracle.STATES))

    def test_80_mock_provider_calls_and_paired_evaluation(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);prepare.prepare(out)
            cases,gold=oracle.validate()
            prepared={prepare.sha(prepare.encoded(x["body"]).encode()):x for x in
                [json.loads(line) for line in (out/"requests.jsonl").read_text().splitlines()]}
            called=[]
            def responder(req,timeout):
                b=json.loads(req.data.decode("utf-8"))
                item=prepared[prepare.sha(prepare.encoded(b).encode())]
                called.append(item["sequence"])
                truth=gold["case_class"][item["id"]]
                if item["condition"].startswith("BINARY"):
                    answers={
                      "h1_supported":{"type":"noul","noul":.9 if truth in ("BOTH","ONLY_H1") else .1},
                      "h2_supported":{"type":"noul","noul":.9 if truth in ("BOTH","ONLY_H2") else .1}
                    }
                else:
                    probs={x:.05 for x in oracle.STATES};probs[truth]=.85
                    answers={"status":{"type":"choice","choice":truth,"probabilities":probs,"confidence":.65}}
                return io.BytesIO(json.dumps({"success":True,"result":{"answers":answers,"usage":{"input_tokens":150}}}).encode())
            outcome=run_cloudflare.run(out,env={
                "EPI06_AUTHORIZATION":"RUN_EPI06_MAX80","CLOUDFLARE_ACCOUNT_ID":"f"*32,
                "CLOUDFLARE_API_TOKEN":"MOCK_ONLY"},sender=responder)
            self.assertEqual((len(called),outcome["calls_succeeded"]),(80,80))
            self.assertEqual(outcome["status"],"COMPLETE")
            report=evaluate.evaluate(out)
            self.assertEqual(len(report["records"]),80)
            for k in prepare.CONDITIONS:
                self.assertEqual(report["by_condition"][k]["n_correct"],20)
                self.assertEqual(report["by_condition"][k]["neither_correct"],8)
                self.assertEqual(report["by_condition"][k]["control_correct"],12)
                self.assertEqual(report["by_condition"][k]["neither_false_support"],0)
            self.assertEqual(report["contrasts"]["difference_in_differences_accuracy"],0)
            self.assertEqual(len(report["paired"]),4)
            self.assertTrue((out/"evaluation-report.json").is_file())

if __name__=="__main__":
    unittest.main()

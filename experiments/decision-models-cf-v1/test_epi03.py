"""EPI-03 no-network, no-cost tests. No production credentials or provider calls."""
from __future__ import annotations
import io,json,sys,tempfile,unittest
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import prepare
import run_cloudflare as runner
import evaluate

class Epi03Tests(unittest.TestCase):
    def test_balanced_gold_and_anchor_provenance(self):
        cases=json.loads(prepare.DECISIONS.read_text(encoding="utf-8"))["cases"]
        gold=json.loads(prepare.GOLD.read_text(encoding="utf-8"))["classification"]
        self.assertEqual(Counter(gold[c["id"]] for c in cases if c["kind"]=="balanced"),
                         Counter({x:3 for x in prepare.OPTIONS}))
        anchors=[c for c in cases if c["kind"]=="epi02_anchor"]
        self.assertEqual(len(anchors),2)
        self.assertTrue(all(c["source_sha"]=="dc62f04bc0498d687c963c941f348dc793fbc9a4" for c in anchors))
        for c in cases:
            self.assertEqual(prepare.closure(c),gold[c["id"]])

    def test_no_gold_in_model_payload_and_same_raw_state(self):
        requests=prepare.make_requests()
        self.assertEqual(len(requests),36)
        self.assertEqual(Counter(r["model"] for r in requests),{"CLEF":14,"GLM":14,"CLAIRIC":8})
        classified={}
        for r in requests:
            if r["type"]!="CLASSIFICATION":continue
            state=r["body"]["state"] if r["model"]=="CLEF" else r["body"]["messages"][0]["content"].split("\nSTATE=",1)[1]
            self.assertNotIn("locked_before_provider",state)
            self.assertNotIn('"gold"',state)
            classified[(r["id"],r["model"])]=state
        for cid,_ in [(r["id"],r["model"]) for r in requests if r["model"]=="CLEF"]:
            self.assertEqual(classified[(cid,"CLEF")],classified[(cid,"GLM")])

    def test_typed_cloudflare_request_contracts(self):
        requests=prepare.make_requests()
        for r in requests:
            if r["model"]=="CLEF":
                self.assertEqual(r["body"]["model"],"clef")
                q=r["body"]["questions"]["support_state"]
                self.assertEqual(q["type"],"choice")
                self.assertEqual(set(q["criteria"]),set(prepare.OPTIONS))
            if r["model"]=="CLAIRIC":
                self.assertEqual(r["body"]["model"],"clairic")
                self.assertIn(r["body"]["fields"]["stock_value"]["type"],("number","estimate"))

    def test_preparation_no_provider_and_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            r=prepare.prepare(p)
            self.assertEqual(r["calls_made"],0)
            self.assertEqual(r["calls_planned"],36)
            self.assertEqual(prepare.sha((p/"requests.jsonl").read_bytes()),r["requests_sha256"])
            self.assertFalse((p/"inference-manifest.json").exists())

    def test_runner_rejects_without_explicit_authorization(self):
        with tempfile.TemporaryDirectory() as d:
            called=[]
            def send(*args,**kwargs):
                called.append(True)
                raise AssertionError("No external calls")
            with self.assertRaises(SystemExit):
                runner.run(Path(d),env={"CLOUDFLARE_ACCOUNT_ID":"test","CLOUDFLARE_API_TOKEN":"test"},sender=send)
            self.assertEqual(called,[])

    def test_probability_brier_and_strict_validation(self):
        probs={"BOTH":0.7,"ONLY_H1":0.1,"ONLY_H2":0.1,"NEITHER":0.1}
        choice,p,err=evaluate.valid_distribution({"choice":"BOTH","probabilities":probs},"GLM")
        self.assertEqual((choice,err),("BOTH",[]))
        self.assertAlmostEqual(evaluate.brier(p,"BOTH"),0.12)
        _,p,err=evaluate.valid_distribution({"choice":"BOTH","probabilities":dict(probs,BOTH=0.5)},"GLM")
        self.assertIsNone(p)
        self.assertIn("PROBABILITIES_NOT_NORMALIZED",err)

    def test_glm_fences_are_flagged_and_clairic_interval(self):
        raw={"response":chr(96)*3+"json\n"+json.dumps({"choice":"ONLY_H1","probabilities":{k:0.25 for k in prepare.OPTIONS}})+"\n"+chr(96)*3}
        obj,flags=evaluate.parse_glm(raw)
        self.assertEqual(obj["choice"],"ONLY_H1")
        self.assertEqual(flags,["FENCED_JSON"])
        self.assertEqual(evaluate.numeric_value({"answers":{"stock_value":{"value":18,"p10":12,"p90":24}}}), (18,[12,24],[]))

    def test_complete_36_mock_calls_and_evaluation(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            prepare.prepare(out)
            calls=[]
            def send(request,timeout):
                self.assertTrue(request.full_url.startswith("https://api.cloudflare.com/client/v4/accounts/"))
                b=json.loads(request.data.decode("utf-8"))
                calls.append(True)
                if b.get("model")=="clef":
                    result={"answers":{"support_state":{"type":"choice","choice":"BOTH",
                             "probabilities":{"BOTH":0.7,"ONLY_H1":0.1,"ONLY_H2":0.1,"NEITHER":0.1},
                             "confidence":0.7}},"usage":{"input_tokens":150,"output_tokens":0}}
                elif b.get("model")=="clairic":
                    result={"answers":{"stock_value":{"type":"estimate","value":15,"p10":10,"p90":20}},
                            "usage":{"input_tokens":140,"output_tokens":0}}
                else:
                    answer={"choice":"BOTH","probabilities":{"BOTH":0.7,"ONLY_H1":0.1,"ONLY_H2":0.1,"NEITHER":0.1}}
                    result={"response":json.dumps(answer),"usage":{"prompt_tokens":300,"completion_tokens":30}}
                return io.BytesIO(json.dumps({"success":True,"result":result}).encode())
            manifest=runner.run(out,env={
                "EPI03_AUTHORIZATION":"RUN_EPI03_MAX36",
                "CLOUDFLARE_ACCOUNT_ID":"f"*32,"CLOUDFLARE_API_TOKEN":"MOCK"
            },sender=send)
            self.assertEqual(len(calls),36)
            self.assertEqual(manifest["status"],"COMPLETE")
            self.assertEqual(manifest["calls_succeeded"],36)
            score=evaluate.evaluate(out)
            self.assertEqual(len(score["classification"]),28)
            self.assertEqual(len(score["numerics"]),8)
            self.assertEqual(score["metrics"]["balanced/CLEF"]["n"],12)
            self.assertEqual(score["metrics"]["balanced/GLM"]["n"],12)
            self.assertEqual(score["metrics"]["CALC/CLAIRIC"]["n"],4)
            self.assertEqual(score["metrics"]["FORECAST/CLAIRIC"]["n"],4)
            self.assertFalse(any(x["issues"] for x in score["classification"]))
            self.assertEqual(score["status"],"COMPLETE")

if __name__=="__main__":
    unittest.main()

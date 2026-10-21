"""EPI-04 offline tests: oracle parity, fairness, no provider, mock end-to-end."""
from __future__ import annotations
import io,json,sys,tempfile,unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import oracle,prepare,run_cloudflare,evaluate

DECISIONS=json.loads(prepare.DECISIONS.read_text(encoding="utf-8"))["cases"]
NUMERICS=json.loads(prepare.NUMERICS.read_text(encoding="utf-8"))["cases"]
GOLD=json.loads(prepare.GOLD.read_text(encoding="utf-8"))

class Epi04Tests(unittest.TestCase):
    def test_independent_exhaustive_and_antichain_parity(self):
        self.assertEqual(len(oracle.validate_all()),20)
        self.assertEqual(Counter(c["motif"] for c in DECISIONS),
                          dict.fromkeys(("branching","chain","shared","nogoods","restoration"),4))
        self.assertEqual(Counter(GOLD["statuses"].values()),dict.fromkeys(oracle.STATES,5))
        for c in DECISIONS:
            status,env=oracle.verified_status(c)
            self.assertEqual(status,GOLD["statuses"][c["id"]])
            self.assertEqual(bool(env["H1"]),status in ("BOTH","ONLY_H1"))
            self.assertEqual(bool(env["H2"]),status in ("BOTH","ONLY_H2"))

    def test_nogoods_do_not_conflate_individual_and_joint_support(self):
        both=next(c for c in DECISIONS if c["motif"]=="nogoods" and GOLD["statuses"][c["id"]]=="BOTH")
        self.assertTrue(both["nogoods"])
        self.assertEqual(oracle.verified_status(both)[0],"BOTH")

    def test_restoration_changes_last_revision_support(self):
        restored=next(c for c in DECISIONS if c["motif"]=="restoration" and GOLD["statuses"][c["id"]]=="BOTH")
        earlier=json.loads(json.dumps(restored))
        earlier["revisions"]=earlier["revisions"][:2]
        earlier["target_revision"]="R1"
        self.assertEqual(oracle.verified_status(earlier)[0],"NEITHER")
        self.assertEqual(oracle.verified_status(restored)[0],"BOTH")
        self.assertTrue(restored["revisions"][-1]["restored"])

    def test_decimal_conservation_and_fixed_numeric_gold(self):
        self.assertEqual(len(NUMERICS),8)
        self.assertEqual(Counter(n["family"] for n in NUMERICS),{"balance":3,"capacity":2,"serial":3})
        for n in NUMERICS:
            self.assertEqual(oracle.calculate_numeric(n),Decimal(str(GOLD["numerics"][n["id"]])))

    def test_preparation_hashes_equal_states_and_no_gold_leak(self):
        requests=prepare.assemble()
        self.assertEqual(len(requests),48)
        self.assertEqual(Counter(r["model"] for r in requests),{"CLEF":20,"GLM":20,"CLAIRIC":8})
        paired={}
        for r in requests:
            if r["model"]=="CLEF":
                s=r["body"]["state"]
            elif r["model"]=="GLM":
                s=r["body"]["messages"][0]["content"].split("\nSTATE=",1)[1]
            else:
                self.assertEqual(r["body"]["fields"]["calculated_value"]["type"],"number")
                continue
            self.assertNotIn("gold",s)
            self.assertNotIn("motif",s)
            self.assertNotIn("environments",s)
            paired[(r["id"],r["model"])]=s
        for c in DECISIONS:
            self.assertEqual(paired[(c["id"],"CLEF")],paired[(c["id"],"GLM")])
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);report=prepare.prepare(out)
            self.assertEqual(report["calls_made"],0)
            self.assertEqual(report["calls_planned"],48)
            self.assertFalse((out/"inference-manifest.json").exists())
            self.assertEqual(prepare.sha((out/"requests.jsonl").read_bytes()),report["requests_sha256"])

    def test_authorization_gate_prevents_all_network_calls(self):
        with tempfile.TemporaryDirectory() as d:
            calls=[]
            def forbidden(*args,**kwargs):
                calls.append(1)
                raise AssertionError("No external call expected")
            with self.assertRaises(SystemExit):
                run_cloudflare.run(Path(d),env={"CLOUDFLARE_ACCOUNT_ID":"x","CLOUDFLARE_API_TOKEN":"y"},sender=forbidden)
            self.assertFalse(calls)

    def test_strict_probabilities_and_disagreement_do_not_replace_oracle(self):
        correct={"BOTH":0.79,"ONLY_H1":0.07,"ONLY_H2":0.07,"NEITHER":0.07}
        choice,probs,issues=evaluate.decode_choice({"choice":"BOTH","probabilities":correct},"GLM")
        self.assertEqual((choice,issues),("BOTH",[]))
        self.assertAlmostEqual(evaluate.brier(probs,"BOTH"),0.0588)
        choice,probs,issues=evaluate.decode_choice({"choice":"BOTH","probabilities":{"BOTH":1.0}},"GLM")
        self.assertIsNone(probs)
        self.assertIn("MISSING_PROBABILITIES",issues)
        a,issues=evaluate.parse_clairic({"answers":{"calculated_value":{"value":999}}})
        self.assertEqual((a,issues),(Decimal("999"),[]))
        self.assertNotEqual(a,oracle.calculate_numeric(NUMERICS[0]))

    def test_full_mock_48_calls_and_scoring_no_network(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)
            prepare.prepare(out)
            prepped={prepare.sha(prepare.dump(r["body"]).encode()):r for r in prepare.assemble()}
            attempts=[]
            def fake_sender(request,timeout):
                body=json.loads(request.data.decode("utf-8"))
                r=prepped[prepare.sha(prepare.dump(body).encode())]
                attempts.append(r)
                if r["model"]=="CLEF":
                    chosen=GOLD["statuses"][r["id"]]
                    probs={s:0.07 for s in oracle.STATES};probs[chosen]=0.79
                    reply={"answers":{"status":{"type":"choice","choice":chosen,"probabilities":probs}},
                           "usage":{"input_tokens":200,"output_tokens":0}}
                elif r["model"]=="GLM":
                    chosen=GOLD["statuses"][r["id"]]
                    probs={s:0.07 for s in oracle.STATES};probs[chosen]=0.79
                    reply={"response":json.dumps({"choice":chosen,"probabilities":probs}),
                           "usage":{"prompt_tokens":250,"completion_tokens":40}}
                else:
                    reply={"answers":{"calculated_value":{"type":"number","value":GOLD["numerics"][r["id"]] }},
                           "usage":{"input_tokens":120,"output_tokens":0}}
                return io.BytesIO(json.dumps({"success":True,"result":reply}).encode())
            manifest=run_cloudflare.run(out,env={
                "EPI04_AUTHORIZATION":"RUN_EPI04_MAX48","CLOUDFLARE_ACCOUNT_ID":"f"*32,
                "CLOUDFLARE_API_TOKEN":"FAKE_TOKEN"},sender=fake_sender)
            self.assertEqual((manifest["calls_succeeded"],len(attempts)),(48,48))
            self.assertEqual(manifest["retry_policy"],"none")
            report=evaluate.evaluate(out)
            self.assertEqual(report["by_model"]["CLEF"]["correct"],20)
            self.assertEqual(report["by_model"]["GLM"]["correct"],20)
            self.assertEqual(report["pairwise"]["both_correct"],20)
            self.assertEqual(report["math_crosscheck_summary"]["matches"],8)
            self.assertFalse(report["math_crosscheck_summary"]["ground_truth_replaced"])
            self.assertEqual(len(report["classification"]),40)
            self.assertEqual(len(report["numeric_crosschecks"]),8)
            self.assertTrue((out/"evaluation-report.json").is_file())

if __name__=="__main__":
    unittest.main()

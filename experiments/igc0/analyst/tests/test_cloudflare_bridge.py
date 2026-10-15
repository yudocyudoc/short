#!/usr/bin/env python3
"""No-cost tests for Cloudflare transport and auditable one-revision runner."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from cloudflare_bridge import make_request, execute, stage_run, submit_worker

PACKET={"case_id":"M01","epistemic":{"counterfactual_without_model":"DESCONOCIDO"},
        "pos_by_arrival_cohort":[],"daily_stocks":[]}
PROMPT="IGC0 graph-only test prompt"
URL="https://igc0.example.workers.dev"
KEY="test-token-abcdefghijklmnopqrstuvwxyz0123456789"
RUN="12345678-1"

class TestCloudflareBridge(unittest.TestCase):
    def test_two_stage_context_replayed_explicitly(self):
        prev={"case_id":"M01","stocks":[]}
        gate={"accepted":False,"issues":[{"code":"DANGLING_INFO_LINK","where":"x"}]}
        request=make_request("REVIEW",PACKET,PROMPT,"igc0-test-0001",prev,gate)
        self.assertEqual(len(request["messages"]),4)
        self.assertEqual([x["role"] for x in request["messages"]],
                         ["system","user","assistant","user"])
        self.assertIn("DANGLING_INFO_LINK",request["messages"][-1]["content"])
        self.assertEqual(json.loads(request["messages"][2]["content"]),prev)
    def test_review_without_prior_model_refused(self):
        with self.assertRaises(ValueError):
            make_request("REVIEW",PACKET,PROMPT,"igc0-test-0002")
    def test_valid_first_graph_skips_second_call(self):
        calls=[]
        def mock(stage,packet,prompt,out,run_id,worker_url,token,previous=None,findings=None):
            calls.append(stage)
            return {"case_id":"M01"},{"accepted":True,"issues":[]}
        with tempfile.TemporaryDirectory() as td,patch("cloudflare_bridge.stage_run",side_effect=mock):
            verdict=execute(PACKET,PROMPT,Path(td),RUN,URL,KEY)
            self.assertEqual(verdict["status"],"IG_ACCEPT")
            self.assertEqual(verdict["actual_inferences"],1)
            self.assertEqual(calls,["IG"])
            self.assertTrue((Path(td)/"summary.json").exists())
    def test_rejected_graph_receives_exactly_one_review(self):
        calls=[]
        initial={"case_id":"M01","stocks":[],"pipes":[]}
        errors={"accepted":False,"issues":[{"code":"MISSING_DOMAIN_STOCK","where":"stocks"}]}
        def mock(stage,packet,prompt,out,run_id,worker_url,token,previous=None,findings=None):
            calls.append(stage)
            if stage=="IG":return initial,errors
            self.assertEqual(previous,initial)
            self.assertEqual(findings,errors)
            return {"case_id":"M01","stocks":[{"id":"orders"}]}, {"accepted":True,"issues":[]}
        with tempfile.TemporaryDirectory() as td,patch("cloudflare_bridge.stage_run",side_effect=mock):
            verdict=execute(PACKET,PROMPT,Path(td),RUN,URL,KEY)
            self.assertEqual(verdict["status"],"REVIEW_ACCEPT")
            self.assertEqual(verdict["actual_inferences"],2)
            self.assertEqual(calls,["IG","REVIEW"])
    def test_invalid_json_stops_without_review(self):
        calls=[]
        def mock(stage,*args,**kwargs):
            calls.append(stage); return None,{"accepted":False}
        with tempfile.TemporaryDirectory() as td,patch("cloudflare_bridge.stage_run",side_effect=mock):
            verdict=execute(PACKET,PROMPT,Path(td),RUN,URL,KEY)
            self.assertEqual(verdict["status"],"IG_FORMAT_OR_TRANSPORT_REJECT")
            self.assertEqual(calls,["IG"])
    def test_worker_reply_correlation_is_mandatory(self):
        body=make_request("IG",PACKET,PROMPT,"igc0-test-0003")
        with patch("cloudflare_bridge.urlopen") as u:
            reply=u.return_value.__enter__.return_value
            reply.read.return_value=b'{"schema_version":"igc0.worker.v1","case_id":"M08","stage":"IG","request_id":"igc0-test-0003","model":"@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"}'
            with self.assertRaises(ValueError):
                submit_worker(URL,KEY,body)
    def test_stage_run_saves_raw_and_never_saves_http_token(self):
        body={"schema_version":"igc0.worker.v1","case_id":"M01","stage":"IG",
              "request_id":"igc0-12345678-1-ig",
              "model":"@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
              "provider_result":{"response":'{"case_id":"M01","stocks":[],"pipes":[]}',
                                 "usage":{"total_tokens":3}}}
        with tempfile.TemporaryDirectory() as td,patch("cloudflare_bridge.submit_worker",return_value=body),patch(
                "cloudflare_bridge.graph_gate",return_value={"accepted":False,"issues":[{"code":"GRAPH_EMPTY"}]}):
            obj,verdict=stage_run("IG",PACKET,PROMPT,Path(td),RUN,URL,KEY)
            self.assertEqual(obj["case_id"],"M01")
            self.assertFalse(verdict["accepted"])
            combined="".join(f.read_text(encoding="utf-8") for f in Path(td).rglob("*") if f.is_file())
            self.assertNotIn(KEY,combined)
            self.assertIn("GRAPH_EMPTY",combined)
if __name__=="__main__":
    unittest.main()

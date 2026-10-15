#!/usr/bin/env python3
"""No-cost tests for Cloudflare transport and auditable single-call R2 runner."""
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
    def test_r2_rejects_review_even_with_previous_model(self):
        prev={"case_id":"M01","stocks":[]}
        gate={"accepted":False,"issues":[{"code":"DANGLING_INFO_LINK","where":"x"}]}
        with self.assertRaises(ValueError):
            make_request("REVIEW",PACKET,PROMPT,"igc0-test-0001",prev,gate)
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
    def test_rejected_graph_stops_after_one_ig_call(self):
        calls=[]
        initial={"case_id":"M01","stocks":[],"pipes":[]}
        errors={"accepted":False,"issues":[{"code":"MISSING_DOMAIN_STOCK","where":"stocks"}]}
        def mock(stage,packet,prompt,out,run_id,worker_url,token,previous=None,findings=None):
            calls.append(stage)
            return initial,errors
        with tempfile.TemporaryDirectory() as td,patch("cloudflare_bridge.stage_run",side_effect=mock):
            verdict=execute(PACKET,PROMPT,Path(td),RUN,URL,KEY)
            self.assertEqual(verdict["status"],"IG_REJECT")
            self.assertEqual(verdict["max_inferences"],1)
            self.assertEqual(verdict["actual_inferences"],1)
            self.assertEqual(calls,["IG"])
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
            reply.read.return_value=b'{"schema_version":"igc0.worker.v1","case_id":"M08","stage":"IG","request_id":"igc0-test-0003","model":"@cf/meta/llama-3.3-70b-instruct-fp8-fast"}'
            with self.assertRaises(ValueError):
                submit_worker(URL,KEY,body)
    def test_stage_run_saves_raw_and_never_saves_http_token(self):
        body={"schema_version":"igc0.worker.v1","case_id":"M01","stage":"IG",
              "request_id":"igc0-12345678-1-ig",
              "model":"@cf/meta/llama-3.3-70b-instruct-fp8-fast",
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

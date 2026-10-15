#!/usr/bin/env python3
"""M01 only: GitHub-owned audited single-call Llama IG inference (M01-R2).

The Worker is a stateless transport to Workers AI. GitHub's Python code owns
all input verification, immutable artifacts and deterministic SD graph checks.
No evaluator oracle or aggregate SD simulator may be used as model input.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from prepare import sha, write
from run_llm import separate
from igc_split_gate import graph_gate

CONTRACT = "igc0.worker.v1"
MODEL = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def decode_provider(answer):
    if not isinstance(answer, dict):
        return None, {}
    if "response" in answer:
        return answer["response"], answer.get("usage", {})
    options = answer.get("choices")
    if isinstance(options, list) and options:
        msg = options[0].get("message", {})
        return msg.get("content"), answer.get("usage", {})
    return None, answer.get("usage", {})

def make_request(stage, packet, prompt, request_id, previous=None, findings=None):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": json.dumps(packet, ensure_ascii=False, sort_keys=True,
                                              separators=(",", ":"))},
    ]
    if stage != "IG":
        raise ValueError("M01-R2 authorizes only the IG stage")
    return {"schema_version": CONTRACT, "case_id": "M01",
            "stage": stage, "request_id": request_id, "messages": messages}

def submit_worker(url, secret, request_body):
    req = Request(url.rstrip("/") + "/v1/infer",
        data=json.dumps(request_body, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={"Authorization": "Bearer " + secret,
                 "Content-Type": "application/json",
                 "User-Agent": "IGC0-GitHub-Audit/1.0"},
        method="POST")
    with urlopen(req, timeout=240) as conn:
        data=json.load(conn)
    if (data.get("schema_version") != CONTRACT or data.get("case_id") != "M01"
        or data.get("stage") != request_body["stage"] or data.get("request_id") != request_body["request_id"]
        or data.get("model") != MODEL):
        raise ValueError("Worker response contract or request correlation mismatch")
    return data

def stage_run(stage, packet, prompt, output, run_id, worker_url, token, previous=None, findings=None):
    path = output / stage
    path.mkdir(parents=True, exist_ok=True)
    req = make_request(stage, packet, prompt, f"igc0-{run_id}-{stage.lower()}",
                       previous=previous, findings=findings)
    # Save the full request without the HTTP authorization header.
    write(path / "request.json", req)
    trace = {"stage": stage, "request_sha256": sha(req),
             "prompt_sha256": digest(prompt), "packet_sha256": sha(packet),
             "request_id": req["request_id"], "retry_count": 0}
    try:
        raw = submit_worker(worker_url, token, req)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        trace["transport_status"] = "REJECT"
        trace["error_type"] = type(exc).__name__
        if isinstance(exc, HTTPError):
            trace["http_status"] = exc.code
        write(path / "transport.json", trace)
        return None, None
    write(path / "worker_response.json", raw)
    final, usage = decode_provider(raw.get("provider_result"))
    if isinstance(final, str):
        (path / "raw_response.txt").write_text(final, encoding="utf-8")
    else:
        write(path / "raw_response.json", final)
    obj, reasoning, kind = separate(final)
    if reasoning is not None:
        (path / "reasoning.txt").write_text(reasoning, encoding="utf-8")
    if obj is not None:
        write(path / "model.json", obj)
        verdict=graph_gate(obj, packet)
    else:
        verdict={"accepted": False, "issues": [
            {"code": "FORMAT_REJECT", "where": "response",
             "detail": "LLM output was not a complete JSON object"}]}
    write(path / "validation.json", verdict)
    trace.update({"transport_status": "OK", "response_format": kind,
                  "accepted": verdict["accepted"], "usage": usage,
                  "response_sha256": sha(raw)})
    write(path / "transport.json", trace)
    return obj, verdict

def execute(packet, prompt, out, run_id, worker_url, token):
    if packet.get("case_id") != "M01":
        raise ValueError("This pilot is restricted to M01")
    if packet.get("epistemic", {}).get("counterfactual_without_model") != "DESCONOCIDO":
        raise ValueError("Public provenance expected")
    out.mkdir(parents=True, exist_ok=True)
    result={"experiment": "IGC0_M01_IG_LLAMA_R2",
            "input_sha256": sha(packet), "prompt_sha256": digest(prompt),
            "source_commit": os.getenv("GITHUB_SHA", "local_test"),
            "github_run_id": run_id,
            "model": MODEL,
            "cloudflare_worker_url": worker_url.rstrip("/"),
            "max_inferences": 1,
            "actual_inferences": 1,
            "has_oracle": False, "projection_permitted": False}
    write(out / "input.json", packet)
    (out / "prompt.md").write_text(prompt, encoding="utf-8")
    initial, first_gate = stage_run("IG",packet,prompt,out,run_id,worker_url,token)
    result["IG_accept"] = bool(first_gate and first_gate.get("accepted"))
    if result["IG_accept"]:
        result["status"] = "IG_ACCEPT"
        result["review_status"] = "NOT_NEEDED"
    elif initial is None:
        result["status"] = "IG_FORMAT_OR_TRANSPORT_REJECT"
        result["review_status"] = "SKIPPED_UNPARSEABLE"
    else:
        result["status"] = "IG_REJECT"
        result["review_status"] = "DISABLED_SINGLE_CALL_R2"
    write(out / "summary.json", result)
    print("IGC0_WORKER_AUDIT_SUMMARY", json.dumps({
        "status":result["status"],"calls":result["actual_inferences"],
        "review":result["review_status"],"input_sha256":result["input_sha256"]
    },ensure_ascii=False),flush=True)
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--inputs",type=Path,required=True)
    ap.add_argument("--prompt",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--run-id",required=True)
    ap.add_argument("--execute",action="store_true",
                    help="Explicit permission for ONE paid Workers AI IG call")
    args=ap.parse_args()
    if not args.execute:
        raise SystemExit("No inference. Pass --execute deliberately.")
    url=os.getenv("IGC_WORKER_URL","").strip()
    secret=os.getenv("IGC_WORKER_API_KEY","").strip()
    if not url.startswith("https://") or len(secret) < 24:
        raise SystemExit("IGC_WORKER_URL HTTPS variable and IGC_WORKER_API_KEY secret required")
    packet=json.loads((args.inputs/"M01.json").read_text(encoding="utf-8"))
    prompt=args.prompt.read_text(encoding="utf-8")
    execute(packet,prompt,args.out,args.run_id,url,secret)

if __name__=="__main__":
    main()

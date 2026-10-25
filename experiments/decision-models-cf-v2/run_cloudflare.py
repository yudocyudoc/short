#!/usr/bin/env python3
"""Authenticated EPI-04 model calls. No retries or silent continuation on failure."""
from __future__ import annotations
import argparse,json,os,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from prepare import ROOT,GOLD,DECISIONS,NUMERICS,MAX_CALLS,MODELS,dump,sha

AUTH="RUN_EPI04_MAX48"
def run(out,env=None,sender=urlopen):
    env=os.environ if env is None else env
    if env.get("EPI04_AUTHORIZATION")!=AUTH:
        raise SystemExit("EPI-04 requires separate explicit RUN_EPI04_MAX48 authorization")
    account=env.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=env.get("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token:
        raise SystemExit("Missing Cloudflare secrets; no calls")
    prep=json.loads((out/"preparation-report.json").read_text(encoding="utf-8"))
    raw=(out/"requests.jsonl").read_bytes()
    if prep["calls_planned"]!=MAX_CALLS or sha(raw)!=prep["requests_sha256"]:
        raise SystemExit("Prepared schedule mismatch")
    for file,key in ((GOLD,"gold_sha256"),(DECISIONS,"decisions_sha256"),(NUMERICS,"math_sha256")):
        if sha(file.read_bytes())!=prep[key]:raise SystemExit("Frozen fixture changed")
    requests=[json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    if len(requests)!=MAX_CALLS or [r["sequence"] for r in requests]!=list(range(1,MAX_CALLS+1)):
        raise SystemExit("Invalid request sequence")
    for r in requests:
        if r["model"] not in MODELS or r["endpoint"]!=MODELS[r["model"]]:
            raise SystemExit("Unapproved model")
        if sha(dump(r["body"]).encode())!=r["body_sha256"]:
            raise SystemExit("Request integrity mismatch")
    out.mkdir(parents=True,exist_ok=True)
    manifest={"schema":"short-epi04-inference/1","started_utc":datetime.now(timezone.utc).isoformat(),
        "status":"INCOMPLETE_NO_RETRY","calls_planned":MAX_CALLS,"calls_attempted":0,"calls_succeeded":0,
        "retry_policy":"none","requests_sha256":prep["requests_sha256"],"runs":[]}
    mpath=out/"inference-manifest.json"
    def persist():
        mpath.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    persist()
    try:
        for r in requests:
            i=r["sequence"]; label=f"{i:02d}-{r['model']}-{r['id']}"
            (out/f"input-{label}.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            endpoint=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODELS[r['model']]}"
            req=Request(endpoint,data=dump(r["body"]).encode("utf-8"),method="POST",
                headers={"Authorization":"Bearer "+token,"Content-Type":"application/json","Accept":"application/json"})
            manifest["calls_attempted"]+=1;persist()
            started=time.monotonic()
            try:
                with sender(req,timeout=150) as response:
                    raw_response=json.load(response)
                if not isinstance(raw_response,dict) or not raw_response.get("success",True):
                    raise ValueError("Provider unsuccessful")
                result=raw_response.get("result",raw_response)
                if not isinstance(result,dict):raise ValueError("Malformed response")
                if r["model"] in ("CLEF","CLAIRIC"):
                    if not isinstance(result.get("answers"),dict):raise ValueError("Missing answers")
                else:
                    if not isinstance(result.get("response"),str) and not isinstance(result.get("choices"),list):
                        raise ValueError("Missing text")
                latency=round((time.monotonic()-started)*1000,1)
                (out/f"raw-{label}.json").write_text(json.dumps(raw_response,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                manifest["runs"].append({k:r[k] for k in ("sequence","id","motif","kind","model")}|{
                    "prefix":label,"status":"OK","latency_ms":latency,
                    "usage":result.get("usage",raw_response.get("usage",{})),
                    "raw_sha256":sha(dump(raw_response).encode())})
                manifest["calls_succeeded"]+=1
                print(f"EPI04_CALL {i}/{MAX_CALLS} {r['model']} {r['id']} OK",flush=True)
                persist()
            except (HTTPError,URLError,TimeoutError,ValueError) as exc:
                manifest["runs"].append({"sequence":i,"id":r["id"],"model":r["model"],
                    "status":"ERROR","error_type":type(exc).__name__,
                    "http_status":exc.code if isinstance(exc,HTTPError) else None})
                persist()
                print(f"EPI04_CALL {i}/{MAX_CALLS} ERROR {type(exc).__name__}; stop, no retry",flush=True)
                break
    finally:
        manifest["status"]="COMPLETE" if manifest["calls_succeeded"]==MAX_CALLS else "INCOMPLETE_NO_RETRY"
        persist()
    if manifest["status"]!="COMPLETE":raise SystemExit("Incomplete inference; no automatic retries")
    return manifest

if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--out",type=Path,default=ROOT/"results")
    run(a.parse_args().out)

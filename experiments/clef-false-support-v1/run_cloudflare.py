#!/usr/bin/env python3
"""EPI-05 separately authorized bounded runner: 48 Clef calls, zero retries."""
from __future__ import annotations
import argparse,json,os,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from oracle import ROOT,FIXTURES,GOLD
from prepare import AUTH,CONDITIONS,MAX_CALLS,MODEL,sha,transport

def run(out,env=None,sender=urlopen):
    env=os.environ if env is None else env
    if env.get("EPI05_AUTHORIZATION")!=AUTH:
        raise SystemExit("NO_INFERENCE: need explicit EPI05_AUTHORIZATION=RUN_EPI05_MAX48")
    account=env.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=env.get("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token:
        raise SystemExit("NO_INFERENCE: Cloudflare credentials absent")
    pre=json.loads((out/"preparation-report.json").read_text(encoding="utf-8"))
    raw=(out/"requests.jsonl").read_bytes()
    if pre["calls_planned"]!=MAX_CALLS or pre["calls_made"]!=0 or sha(raw)!=pre["requests_sha256"]:
        raise SystemExit("NO_INFERENCE: prepared experiment mismatch")
    if sha(FIXTURES.read_bytes())!=pre["fixture_sha256"] or sha(GOLD.read_bytes())!=pre["gold_sha256"]:
        raise SystemExit("NO_INFERENCE: frozen input/gold changed")
    requests=[json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    if len(requests)!=MAX_CALLS or [r["sequence"] for r in requests]!=list(range(1,MAX_CALLS+1)):
        raise SystemExit("NO_INFERENCE: invalid call count or order")
    for r in requests:
        if r["condition"] not in CONDITIONS or r["model"]!="CLEF" or r["endpoint"]!=MODEL:
            raise SystemExit("NO_INFERENCE: unapproved model or condition")
        if sha(transport(r["body"]).encode())!=r["body_sha256"]:
            raise SystemExit("NO_INFERENCE: request hash mismatch")
    endpoint=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    out.mkdir(parents=True,exist_ok=True)
    manifest={"schema":"short-epi05-inference/1",
              "started_utc":datetime.now(timezone.utc).isoformat(),
              "status":"INCOMPLETE_NO_RETRY","calls_planned":MAX_CALLS,
              "calls_attempted":0,"calls_succeeded":0,"retry_policy":"none",
              "requests_sha256":pre["requests_sha256"],"records":[]}
    mpath=out/"inference-manifest.json"
    def persist(): mpath.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    persist()
    try:
        for r in requests:
            seq=r["sequence"];prefix=f"{seq:02d}-{r['condition']}-{r['id']}"
            (out/("input-"+prefix+".json")).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            req=Request(endpoint,data=transport(r["body"]).encode(),
                headers={"Authorization":"Bearer "+token,"Content-Type":"application/json","Accept":"application/json"},
                method="POST")
            manifest["calls_attempted"]+=1;persist()
            start=time.monotonic()
            try:
                with sender(req,timeout=150) as response:
                    raw_response=json.load(response)
                if not isinstance(raw_response,dict) or not raw_response.get("success",True):
                    raise ValueError("Provider returned unsuccessful response")
                result=raw_response.get("result",raw_response)
                if not isinstance(result,dict) or not isinstance(result.get("answers"),dict):
                    raise ValueError("Clef answer missing")
                latency=round((time.monotonic()-start)*1000,1)
                (out/("raw-"+prefix+".json")).write_text(json.dumps(raw_response,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                row={k:r[k] for k in ("sequence","id","source_motif","condition")}
                row.update({"prefix":prefix,"status":"OK","latency_ms":latency,
                            "usage":result.get("usage",raw_response.get("usage",{})),
                            "response_sha256":sha(transport(raw_response).encode())})
                manifest["records"].append(row)
                manifest["calls_succeeded"]+=1
                print(f"EPI05_CALL {seq}/{MAX_CALLS} {r['condition']} {r['id']} OK",flush=True)
                persist()
            except (HTTPError,URLError,TimeoutError,ValueError) as exc:
                manifest["records"].append({"sequence":seq,"id":r["id"],"condition":r["condition"],
                  "status":"ERROR","error_type":type(exc).__name__,
                  "http_status":exc.code if isinstance(exc,HTTPError) else None})
                persist()
                print(f"EPI05_CALL {seq}/{MAX_CALLS} ERROR {type(exc).__name__}; no retry",flush=True)
                break
    finally:
        manifest["status"]="COMPLETE" if manifest["calls_succeeded"]==MAX_CALLS else "INCOMPLETE_NO_RETRY"
        persist()
    if manifest["status"]!="COMPLETE":
        raise SystemExit("Incomplete campaign: no retries")
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=ROOT/"results")
    run(p.parse_args().out)

#!/usr/bin/env python3
"""Authorized, bounded Workers AI EPI-03 runner: never called by CI."""
from __future__ import annotations
import argparse, hashlib, json, os, random, time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from prepare import HERE,GOLD,DECISIONS,NUMERICS,MAX_CALLS,MODELS,dump,sha

AUTH="RUN_EPI03_MAX36"
def run(out, env=None, sender=urlopen):
    env=os.environ if env is None else env
    if env.get("EPI03_AUTHORIZATION")!=AUTH:
        raise SystemExit("NO_INFERENCE: EPI03_AUTHORIZATION must equal RUN_EPI03_MAX36")
    account=env.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=env.get("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token:
        raise SystemExit("NO_INFERENCE: missing secrets")
    report=json.loads((out/"preparation-report.json").read_text(encoding="utf-8"))
    if report["calls_planned"]!=MAX_CALLS or report["gold_sha256"]!=sha(GOLD.read_bytes()):
        raise SystemExit("Frozen gold or call count changed; no inference")
    if report["decision_cases_sha256"]!=sha(DECISIONS.read_bytes()) or report["numeric_cases_sha256"]!=sha(NUMERICS.read_bytes()):
        raise SystemExit("Frozen fixtures changed; no inference")
    requests_blob=(out/"requests.jsonl").read_bytes()
    if sha(requests_blob)!=report["requests_sha256"]:
        raise SystemExit("Prepared requests changed; no inference")
    records=[json.loads(x) for x in requests_blob.decode("utf-8").splitlines() if x]
    if len(records)!=MAX_CALLS or len({r["sequence"] for r in records})!=MAX_CALLS:
        raise SystemExit("Invalid schedule")
    for r in records:
        if r["model"] not in MODELS or r["endpoint"]!=MODELS[r["model"]]:
            raise SystemExit("Unknown model")
        if r["body_sha256"]!=sha(dump(r["body"]).encode()):
            raise SystemExit("Request integrity failure")
    # No URL, endpoint, or credential is configurable from fixture text.
    out.mkdir(parents=True,exist_ok=True)
    manifest={"schema":"short-epi03-manifest/1","status":"INCOMPLETE_NO_RETRY",
        "date_utc":datetime.now(timezone.utc).isoformat(),"calls_attempted":0,"calls_succeeded":0,
        "calls_planned":MAX_CALLS,"retry_policy":"none","prepared_sha256":report["requests_sha256"],
        "records":[]}
    target=out/"inference-manifest.json"
    def persist():
        target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    persist()
    try:
        for r in records:
            i=r["sequence"]
            name=f"{i:02d}-{r['model']}-{r['id']}"
            endpoint=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODELS[r['model']]}"
            (out/f"input-{name}.json").write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            payload=dump(r["body"]).encode("utf-8")
            req=Request(endpoint,data=payload,headers={"Authorization":f"Bearer {token}",
                "Content-Type":"application/json","Accept":"application/json"},method="POST")
            manifest["calls_attempted"]+=1
            persist()
            started=time.monotonic()
            try:
                with sender(req,timeout=150) as response:
                    raw=json.load(response)
                if not isinstance(raw,dict) or not raw.get("success",True):
                    raise ValueError("Cloudflare unsuccessful response")
                result=raw.get("result",raw)
                if not isinstance(result,dict):
                    raise ValueError("Invalid response shape")
                if r["model"] in ("CLEF","CLAIRIC"):
                    if not isinstance(result.get("answers"),dict):
                        raise ValueError("Decision/extraction answer missing")
                else:
                    if not isinstance(result.get("response"),str) and not isinstance(result.get("choices"),list):
                        raise ValueError("Generative response missing")
                latency=round((time.monotonic()-started)*1000,1)
                (out/f"raw-{name}.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                entry={k:r[k] for k in ("id","type","stratum","model","sequence")}
                entry.update({"status":"OK","prefix":name,"latency_ms":latency,"usage":result.get("usage",raw.get("usage",{})),
                              "response_sha256":sha(dump(raw).encode())})
                manifest["records"].append(entry)
                manifest["calls_succeeded"]+=1
                print(f"EPI03 {i}/{MAX_CALLS} {r['model']} {r['id']} OK",flush=True)
                persist()
            except (HTTPError,URLError,TimeoutError,ValueError) as exc:
                manifest["records"].append({"id":r["id"],"model":r["model"],"sequence":i,
                    "status":"ERROR","error_type":type(exc).__name__,
                    "http_status":exc.code if isinstance(exc,HTTPError) else None})
                print(f"EPI03 stopped on call {i} ({type(exc).__name__}), no retry",flush=True)
                persist()
                break
    finally:
        manifest["status"]="COMPLETE" if manifest["calls_succeeded"]==MAX_CALLS else "INCOMPLETE_NO_RETRY"
        persist()
    if manifest["status"]!="COMPLETE":
        raise SystemExit("Incomplete run; no automatic retries")
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=HERE/"results")
    run(p.parse_args().out)

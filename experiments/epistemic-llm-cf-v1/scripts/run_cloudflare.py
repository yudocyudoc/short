#!/usr/bin/env python3
"""Explicitly authorized EPI-01 pilot: max nine calls, no retries."""
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
HERE=Path(__file__).resolve().parents[1]
MODEL="@cf/zai-org/glm-4.7-flash"; AUTH="RUN_EPI01_MAX9"; MAX_CALLS=9
TEMPERATURE=0.1; MAX_TOKENS=1200; ARMS=("A","B","C")
def sha(b): return hashlib.sha256(b).hexdigest()
def extract(result):
    if isinstance(result,dict):
        if isinstance(result.get("response"),str): return result["response"]
        choices=result.get("choices")
        if isinstance(choices,list) and choices:
            first=choices[0]
            if isinstance(first.get("message"),dict): return first["message"].get("content","")
            return first.get("text","")
    return result if isinstance(result,str) else ""
def run(experiment_dir,out_dir,env=None,request_sender=urlopen):
    env=env or os.environ
    if env.get("EPI01_AUTHORIZATION")!=AUTH: raise SystemExit("Inference refused: explicit authorization is required.")
    account=env.get("CLOUDFLARE_ACCOUNT_ID","").strip(); token=env.get("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token: raise SystemExit("Inference refused: required Actions secrets unavailable.")
    case=json.loads((experiment_dir/"case.json").read_text(encoding="utf-8"))
    common=(experiment_dir/"prompts/common.md").read_text(encoding="utf-8")
    contexts={arm:json.loads((out_dir/f"context-{arm}.json").read_text(encoding="utf-8")) for arm in ARMS}
    schedule=[(arm,task) for task in case["tasks"] for arm in ARMS]
    if len(schedule)!=MAX_CALLS: raise SystemExit("Refused: frozen EPI-01 must contain exactly nine calls.")
    endpoint=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    out_dir.mkdir(parents=True,exist_ok=True)
    manifest={"experiment":"EPI-01","model":MODEL,"date_utc":datetime.now(timezone.utc).isoformat(),
      "temperature":TEMPERATURE,"max_completion_tokens":MAX_TOKENS,"max_calls":MAX_CALLS,
      "calls_attempted":0,"calls_succeeded":0,"retry_policy":"none",
      "order":[{"call":i+1,"arm":arm,"task_id":task["id"]} for i,(arm,task) in enumerate(schedule)],
      "context_sha256":{a:sha((out_dir/f"context-{a}.json").read_bytes()) for a in ARMS},"results":[]}
    for i,(arm,task) in enumerate(schedule,1):
        prompt=common+"\n\n### Expediente del brazo "+arm+"\n"+json.dumps(contexts[arm],ensure_ascii=False,separators=(",",":"))+"\n\n### Tarea\n"+task["id"]+": "+task["question"]
        body=json.dumps({"messages":[{"role":"user","content":prompt}],"temperature":TEMPERATURE,
          "max_completion_tokens":MAX_TOKENS,"chat_template_kwargs":{"enable_thinking":False}},ensure_ascii=False).encode("utf-8")
        req=Request(endpoint,data=body,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},method="POST")
        (out_dir/f"input-{i:02d}-{arm}-{task['id']}.json").write_text(
          json.dumps({"model":MODEL,"arm":arm,"task_id":task["id"],"prompt":prompt,"sha256":sha(prompt.encode())},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        manifest["calls_attempted"]+=1
        try:
            with request_sender(req,timeout=150) as response: raw=json.load(response)
            result=raw.get("result",raw); answer=extract(result)
            if not raw.get("success",True) or not answer.strip(): raise RuntimeError("Provider returned unsuccessful or empty response.")
            (out_dir/f"response-{i:02d}-{arm}-{task['id']}.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            (out_dir/f"answer-{i:02d}-{arm}-{task['id']}.txt").write_text(answer,encoding="utf-8")
            usage=result.get("usage",raw.get("usage",{})) if isinstance(result,dict) else {}
            manifest["calls_succeeded"]+=1
            manifest["results"].append({"call":i,"arm":arm,"task_id":task["id"],"status":"ok","response_sha256":sha(answer.encode()),"usage":usage})
            print(f"EPI01_CALL {i}/{MAX_CALLS} {arm}/{task['id']} success usage={json.dumps(usage)}",flush=True)
        except HTTPError as exc:
            body=exc.read().decode("utf-8","replace").replace(token,"[REDACTED]").replace(account,"[REDACTED]")
            manifest["results"].append({"call":i,"arm":arm,"task_id":task["id"],"status":"http_error","http_status":exc.code,"error":body[:500]})
            print(f"EPI01_CALL {i}/{MAX_CALLS} stopped after HTTP {exc.code}; response withheld from logs.",flush=True); break
        except (URLError,TimeoutError,ValueError,RuntimeError) as exc:
            safe=str(exc).replace(token,"[REDACTED]").replace(account,"[REDACTED]")
            manifest["results"].append({"call":i,"arm":arm,"task_id":task["id"],"status":"error","error":safe[:300]})
            print(f"EPI01_CALL {i}/{MAX_CALLS} stopped ({exc.__class__.__name__}); no retry.",flush=True); break
    manifest["status"]="COMPLETE" if manifest["calls_succeeded"]==MAX_CALLS else "INCOMPLETE_NO_RETRY"
    (out_dir/"inference-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if manifest["status"]!="COMPLETE": raise SystemExit("Pilot incomplete; inspect sanitized artifact; no automatic retries.")
    return manifest
if __name__=="__main__": run(HERE,HERE/"results")

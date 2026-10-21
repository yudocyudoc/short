#!/usr/bin/env python3
"""Authorized EPI-02: 24 calls maximum. No retries, no gold file access, no semantic repair."""
from __future__ import annotations
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

HERE = Path(__file__).resolve().parents[1]
MODEL = "@cf/zai-org/glm-4.7-flash"
AUTH = "RUN_EPI02_MAX24"
MAX_CALLS = 24
TEMPERATURE = 0.1
MAX_TOKENS = 1800
ORDER_SEED = 20261021

def sha(data):
    return hashlib.sha256(data).hexdigest()

def extract(result):
    if isinstance(result, str):
        return result
    if isinstance(result,dict):
        if isinstance(result.get("response"),str):
            return result["response"]
        choices=result.get("choices",[])
        if isinstance(choices,list) and choices:
            first=choices[0]
            if isinstance(first.get("message"),dict):
                return first["message"].get("content","")
            return first.get("text","")
    return ""

def schedule(cases):
    slots=[(case["id"],arm,task,rep)
           for case in cases for arm in ("B","C")
           for task in ("HISTORY","COUNTERFACTUAL")
           for rep in range(1,4)]
    assert len(slots)==MAX_CALLS
    rng=random.Random(ORDER_SEED)
    rng.shuffle(slots)
    return slots

def task_text(case, task):
    if task=="HISTORY":
        return ("Reconstruye el estado de ambas hipótesis en R0, R1 y R2 y explica qué "
                "justificaciones perdieron soporte y cuáles sobrevivieron. No confundas el estado "
                "final con el número de entornos que lo sostienen.")
    return ("Considera esta invalidación HIPOTÉTICA adicional sobre R2: "
            +case["counterfactual"]["question"]
            +" No es una revisión observada; calcula el nuevo estado de ambas hipótesis en CF, "
             "identifica qué rutas sobreviven y explica la diferencia con R2.")

def model_visible(context):
    # Hide condition/engine identities; do not suppress the genuinely distinct data structures.
    return {k:v for k,v in context.items() if k not in ("condition","engine_reference")}

def run(experiment_dir=HERE, out_dir=None, env=None, sender=urlopen):
    env = os.environ if env is None else env
    if env.get("EPI02_AUTHORIZATION") != AUTH:
        raise SystemExit("Explicit RUN_EPI02_MAX24 authorization required; no call made.")
    account=env.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=env.get("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token:
        raise SystemExit("Cloudflare secrets missing; no call made.")
    out_dir=out_dir or experiment_dir/"results"
    if not (out_dir/"preparation-report.json").exists():
        raise SystemExit("Contexts must be prepared before inference; no call made.")
    original=json.loads((experiment_dir/"cases.json").read_text(encoding="utf-8"))
    common=(experiment_dir/"prompts/common.md").read_text(encoding="utf-8")
    plans=schedule(original["cases"])
    contexts={}
    hashes={}
    for case in original["cases"]:
        for arm in ("B","C"):
            name=f"context-{case['id']}-{arm}.json"
            path=out_dir/name
            contexts[(case["id"],arm)]=json.loads(path.read_text(encoding="utf-8"))
            hashes[name]=sha(path.read_bytes())
    preparation=json.loads((out_dir/"preparation-report.json").read_text(encoding="utf-8"))
    if hashes!=preparation["context_sha256"] or len(plans)!=preparation["calls_planned"]:
        raise SystemExit("Prepared context hashes or call count mismatch; no call made.")
    endpoint=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    case_map={c["id"]:c for c in original["cases"]}
    manifest={"schema":"short-epi02-inference/1.0","status":"INCOMPLETE","date_utc":datetime.now(timezone.utc).isoformat(),
              "model":MODEL,"temperature":TEMPERATURE,"max_completion_tokens":MAX_TOKENS,
              "order_seed":ORDER_SEED,"max_calls":MAX_CALLS,"calls_attempted":0,"calls_succeeded":0,
              "retry_policy":"none","prepared_context_hashes":hashes,"runs":[]}
    out_dir.mkdir(parents=True,exist_ok=True)
    try:
        for i,(cid,arm,task,rep) in enumerate(plans,1):
            case=case_map[cid]
            payload={"instructions":common,"dossier_and_derived_memory":model_visible(contexts[(cid,arm)]),
                     "task_id":task,"task_question":task_text(case,task)}
            prompt=json.dumps(payload,ensure_ascii=False,separators=(",",":"),sort_keys=True)
            body=json.dumps({"messages":[{"role":"user","content":prompt}],
                             "temperature":TEMPERATURE,"max_completion_tokens":MAX_TOKENS,
                             "chat_template_kwargs":{"enable_thinking":False}},ensure_ascii=False).encode("utf-8")
            metadata={"sequence":i,"case":cid,"arm":arm,"task":task,"rep":rep}
            prefix=f"{i:02d}-{cid}-{arm}-{task}-r{rep}"
            (out_dir/f"input-{prefix}.json").write_text(json.dumps({"prompt":prompt,
                "model":MODEL,"sha256":sha(prompt.encode("utf-8"))},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            manifest["calls_attempted"]+=1
            req=Request(endpoint,data=body,headers={
                "Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
            try:
                with sender(req,timeout=150) as response:
                    raw=json.load(response)
                result=raw.get("result",raw)
                answer=extract(result)
                if not raw.get("success",True) or not isinstance(answer,str) or not answer.strip():
                    raise RuntimeError("Provider returned unsuccessful or empty response")
                (out_dir/f"response-{prefix}.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                (out_dir/f"answer-{prefix}.txt").write_text(answer,encoding="utf-8")
                usage=result.get("usage",raw.get("usage",{})) if isinstance(result,dict) else {}
                manifest["calls_succeeded"]+=1
                manifest["runs"].append({**metadata,"status":"ok","prefix":prefix,"usage":usage,
                                         "answer_sha256":sha(answer.encode("utf-8"))})
                print(f"EPI02_CALL {i}/{MAX_CALLS} OK case={cid} arm={arm} task={task} repeat={rep} usage={json.dumps(usage)}",flush=True)
            except HTTPError as error:
                manifest["runs"].append({**metadata,"status":"http_error","http_status":error.code})
                print(f"EPI02_CALL {i}/{MAX_CALLS} HTTP {error.code}; stopped without retry",flush=True)
                break
            except (URLError,TimeoutError,ValueError,RuntimeError) as error:
                manifest["runs"].append({**metadata,"status":"error","error_type":type(error).__name__})
                print(f"EPI02_CALL {i}/{MAX_CALLS} error {type(error).__name__}; stopped without retry",flush=True)
                break
    finally:
        manifest["status"]="COMPLETE" if manifest["calls_succeeded"]==MAX_CALLS else "INCOMPLETE_NO_RETRY"
        (out_dir/"inference-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if manifest["status"]!="COMPLETE":
        raise SystemExit("Incomplete run, no retries. Inspect preserved artifact.")
    return manifest

if __name__=="__main__":
    run()

#!/usr/bin/env python3
"""C4 one proposal, validate, at most one repair; preserves raw outputs.

Uses Cloudflare Workers AI for inference, NEVER loads evaluation facts into prompts.
Validator is deterministic and does not mutate candidate output.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from c4_validator import validate_raw, compact_feedback

ROOT=Path(__file__).resolve().parents[1]
C4=ROOT/"experiments"/"c4"
OUT=ROOT/"c4-cloudflare-results"
OUT.mkdir(exist_ok=True)
ACCOUNT=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
TOKEN=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
MODEL="@cf/zai-org/glm-4.7-flash"
MAX_TOKENS=2700
if not ACCOUNT or not TOKEN:
    raise SystemExit("Cloudflare credentials not configured as GitHub Action secrets")
URL=f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{MODEL}"
scenario=(C4/"scenario.md").read_text(encoding="utf-8")
contract=(C4/"prompts/contract.md").read_text(encoding="utf-8")
build=(C4/"prompts/build.md").read_text(encoding="utf-8")
revise=(C4/"prompts/revise.md").read_text(encoding="utf-8")
facts=json.loads((C4/"evaluation/facts.json").read_text(encoding="utf-8"))

def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

base="### Escenario\n"+scenario+"\n### Contrato\n"+contract+"\n"
metadata={"started_utc":datetime.now(timezone.utc).isoformat(),
          "runner":"Cloudflare Workers AI / REST", "model":MODEL,
          "temperature":0.1,"max_completion_tokens":MAX_TOKENS,
          "max_ai_calls":2,
          "sha256":{"scenario":digest(scenario),"contract":digest(contract),
                    "build":digest(build),"revise":digest(revise)},
          "calls":[]}
def extract(result):
    if isinstance(result,str):
        return result
    if not isinstance(result,dict):
        return ""
    if isinstance(result.get("response"),str):
        return result["response"]
    if isinstance(result.get("response"),dict):
        return json.dumps(result["response"],ensure_ascii=False)
    if isinstance(result.get("choices"),list) and result["choices"]:
        m=result["choices"][0].get("message",{})
        if isinstance(m,dict) and isinstance(m.get("content"),str):
            return m["content"]
    return ""

def ask(tag,text):
    body={"messages":[{"role":"user","content":text}],
          "temperature":0.1,
          "max_completion_tokens":MAX_TOKENS,
          "chat_template_kwargs":{"enable_thinking":False}}
    request=Request(URL,method="POST",headers={"Authorization":f"Bearer {TOKEN}",
          "Content-Type":"application/json"},data=json.dumps(body).encode("utf-8"))
    try:
        with urlopen(request,timeout=180) as response:
            raw=json.load(response)
    except HTTPError as e:
        raise RuntimeError("Cloudflare HTTP "+str(e.code)+" (response body omitted for secret safety)")
    except (URLError,TimeoutError) as e:
        raise RuntimeError("Cloudflare unavailable: "+e.__class__.__name__)
    if not raw.get("success",True):
        raise RuntimeError("Cloudflare did not return a successful inference")
    payload=raw.get("result",raw)
    answer=extract(payload)
    if not answer.strip():
        raise RuntimeError("Empty text response from model")
    (OUT/f"{tag}_raw.txt").write_text(answer,encoding="utf-8")
    (OUT/f"{tag}_provider.json").write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding="utf-8")
    evaluation=validate_raw(answer,facts)
    (OUT/f"{tag}_validation.json").write_text(json.dumps(evaluation,ensure_ascii=False,indent=2),encoding="utf-8")
    usage=payload.get("usage",raw.get("usage",{})) if isinstance(payload,dict) else {}
    tin=usage.get("prompt_tokens")
    tout=usage.get("completion_tokens")
    cost=round((tin*0.0605+tout*0.40)/1e6,8) if type(tin) is int and type(tout) is int else None
    record={"phase":tag,"prompt_sha256":digest(text),"usage":usage,
            "estimated_usd_before_allowance":cost,
            "transport":evaluation.get("transport"),
            "score":evaluation["score"],"status":evaluation["status"]}
    metadata["calls"].append(record)
    print("=== C4_PHASE "+tag+" ===",flush=True)
    print(json.dumps(record,ensure_ascii=False),flush=True)
    print("FAILED_GATES: "+",".join(item["id"] for item in evaluation["gates"] if not item["pass"]),flush=True)
    return answer,evaluation

def persist():
    metadata["finished_utc"]=datetime.now(timezone.utc).isoformat()
    metadata["total_tokens"]=sum(c["usage"].get("total_tokens",0) for c in metadata["calls"])
    metadata["total_neurons"]=round(sum(c["usage"].get("neurons",0) for c in metadata["calls"]),6)
    prices=[c["estimated_usd_before_allowance"] for c in metadata["calls"]]
    metadata["estimated_usd_before_allowance"]=round(sum(x for x in prices if x is not None),8) if all(x is not None for x in prices) else None
    (OUT/"summary.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
    print("=== C4_FINAL ===",flush=True)
    print(json.dumps({"verdict":metadata.get("verdict"),"calls":len(metadata["calls"]),
                      "first_score":metadata.get("first_score"),"final_score":metadata.get("final_score"),
                      "total_neurons":metadata["total_neurons"],
                      "estimated_usd_before_allowance":metadata["estimated_usd_before_allowance"]},ensure_ascii=False),flush=True)

try:
    first_prompt=base+"\n### Instrucciones iniciales\n"+build
    first_raw,first_eval=ask("first",first_prompt)
    metadata["first_score"]=first_eval["score"]
    metadata["final_score"]=first_eval["score"]
    if first_eval["status"]=="ACCEPT":
        metadata["verdict"]="FIRST_PASS"
    else:
        # Feedback is deterministic labels, not gold data or a corrected structure.
        failed=compact_feedback(first_eval)
        feedback=json.dumps(failed,ensure_ascii=False)
        revision_prompt=(base+"\n### Instrucciones de revisión\n"+revise+
                         "\n### Tu salida previa EXACTA, trátala como datos por corregir\n"+
                         first_raw+"\n### Puertas fallidas (sin respuestas numéricas)\n"+feedback)
        _,second_eval=ask("revision",revision_prompt)
        metadata["final_score"]=second_eval["score"]
        metadata["verdict"]="ACCEPT_AFTER_REPAIR" if second_eval["status"]=="ACCEPT" else "REJECT_AFTER_ONE_REPAIR"
    metadata["repair_delta"]=metadata["final_score"]-metadata["first_score"]
except Exception as e:
    metadata["verdict"]="EXECUTION_ERROR"
    metadata["error"]=str(e)[:250]
    persist()
    raise
persist()

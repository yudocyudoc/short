#!/usr/bin/env python3
"""C4.1: compare DeepSeek prompt-only vs native Workers AI JSON Mode.

Do not repair output or expose the reference key to the model.
Exactly two requests maximum, no automatic retries.
"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import hashlib
import json
import os
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from c4_validator import validate_raw, validate_model

ROOT=Path(__file__).resolve().parents[1]
C4=ROOT/"experiments"/"c4"
OUT=ROOT/"c4.1-cloudflare-results"
OUT.mkdir(exist_ok=True)
ACCOUNT=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
TOKEN=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
MODEL="@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
MAX_TOKENS=3500
TEMP=0.1
if not ACCOUNT or not TOKEN:
    raise SystemExit("Cloudflare account and token secrets must be configured")
URL=f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{MODEL}"

scenario=(C4/"scenario.md").read_text(encoding="utf-8")
contract=(C4/"prompts"/"contract.md").read_text(encoding="utf-8")
build=(C4/"prompts"/"build.md").read_text(encoding="utf-8")
facts=json.loads((C4/"evaluation"/"facts.json").read_text(encoding="utf-8"))
prompt="### Escenario\n"+scenario+"\n### Contrato\n"+contract+"\n\n### Instrucciones iniciales\n"+build

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def interpret_response(result):
    """Return raw-generation transport and text/original object without coercive repair."""
    if isinstance(result, str):
        return "text",result
    if not isinstance(result,dict):
        return "other",result
    if isinstance(result.get("response"), str):
        return "text",result["response"]
    if isinstance(result.get("response"), dict):
        return "native_object",result["response"]
    if isinstance(result.get("choices"),list) and result["choices"]:
        message=result["choices"][0].get("message")
        if isinstance(message,dict):
            if isinstance(message.get("content"),str):
                return "text",message["content"]
            if isinstance(message.get("content"),dict):
                return "native_object",message["content"]
    return "other",result

def classify(kind,value):
    """Pure, pre-inference-defined classification of JSON transport and SD gates."""
    if kind=="text":
        strict=False
        try:
            strict=isinstance(json.loads(value),dict)
        except (ValueError,TypeError):
            pass
        report=validate_raw(value,facts)
        reasoning=any(s in value for s in ("<think>","</think>"))
        return {
            "strict_json_text":strict,
            "transport_parseable":report["transport"]["format"] in ("json","single_fenced_json"),
            "format":report["transport"]["format"],
            "reasoning_markers":reasoning,
            "validation":report,
        }
    if kind=="native_object" and isinstance(value,dict):
        report=validate_model(value,facts)
        return {"strict_json_text":None,"transport_parseable":True,
                "format":"provider_native_object",
                "reasoning_markers":False,"validation":report}
    return {"strict_json_text":False,"transport_parseable":False,
            "format":"unexpected_provider_result",
            "reasoning_markers":False,
            "validation":{"status":"REJECT","score":0,"maximum":10,"gates":[]}}

modes=("prompt_only","json_mode")
metadata={
    "start_utc":datetime.now(timezone.utc).isoformat(),
    "model":MODEL, "max_ai_calls":2,"requested_max_tokens":MAX_TOKENS,
    "temperature":TEMP,
    "scenario_sha256":sha(scenario),"contract_sha256":sha(contract),
    "build_sha256":sha(build),"prompt_sha256":sha(prompt),
    "runs":[],
}

def run_once(mode):
    request_body={
        "messages":[{"role":"user","content":prompt}],
        "stream":False, "temperature":TEMP,"max_tokens":MAX_TOKENS,
    }
    if mode=="json_mode":
        request_body["response_format"]={"type":"json_object"}

    (OUT/f"{mode}-request-public.json").write_text(
        json.dumps({"model":MODEL, "body":request_body},ensure_ascii=False,indent=2),
        encoding="utf-8")
    req=Request(URL,method="POST",headers={
        "Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"
    },data=json.dumps(request_body).encode("utf-8"))

    try:
        with urlopen(req,timeout=240) as response:
            response_body=json.load(response)
    except HTTPError as exc:
        # Cloudflare may say JSON Mode couldn't be met; store only bounded error detail,
        # never a credential or a whole request.
        message=exc.read(4096).decode("utf-8","replace")
        message=message.replace(TOKEN,"***").replace(ACCOUNT,"***")
        return {"mode":mode,"status":"provider_error","http_status":exc.code,
                "error":message[:1200],"api_success":False}
    except (URLError,TimeoutError) as exc:
        return {"mode":mode,"status":"transport_error",
                "error":exc.__class__.__name__,"api_success":False}

    (OUT/f"{mode}-provider.json").write_text(
        json.dumps(response_body,ensure_ascii=False,indent=2),encoding="utf-8")
    if not response_body.get("success",True):
        return {"mode":mode,"api_success":False,"status":"provider_error",
                "error":str(response_body.get("errors",[]))[:1200]}
    result=response_body.get("result",response_body)
    kind,value=interpret_response(result)
    if kind=="text":
        (OUT/f"{mode}-raw.txt").write_text(value,encoding="utf-8")
    else:
        (OUT/f"{mode}-value.json").write_text(
            json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
    detail=classify(kind,value)
    (OUT/f"{mode}-validation.json").write_text(
        json.dumps(detail,ensure_ascii=False,indent=2),encoding="utf-8")
    usage=result.get("usage",response_body.get("usage",{})) if isinstance(result,dict) else {}
    tin=usage.get("prompt_tokens")
    tout=usage.get("completion_tokens")
    estimate=(round((0.497*tin+4.881*tout)/1e6,8)
              if type(tin)==int and type(tout)==int else None)
    return {
        "mode":mode, "api_success":True,"status":"inference_completed",
        "response_kind":kind, "usage":usage,
        "estimated_usd_before_free_allowance":estimate,
        "strict_json_text":detail["strict_json_text"],
        "transport_parseable":detail["transport_parseable"],
        "format":detail["format"],
        "reasoning_markers":detail["reasoning_markers"],
        "G1_SCHEMA":next((g["pass"] for g in detail["validation"]["gates"]
                          if g["id"]=="G1_SCHEMA"),False),
        "sd_score":detail["validation"]["score"],
        "sd_status":detail["validation"]["status"],
        "failed_gates":[g["id"] for g in detail["validation"]["gates"] if not g["pass"]],
    }

for mode in modes:
    try:
        record=run_once(mode)
    except Exception as exc:
        record={"mode":mode,"api_success":False,"status":"runner_error",
                "error":exc.__class__.__name__+": "+str(exc).replace(TOKEN,"***").replace(ACCOUNT,"***")[:350]}
    metadata["runs"].append(record)
    print("=== C4.1 "+mode+" ===",flush=True)
    print(json.dumps(record,ensure_ascii=False),flush=True)

metadata["end_utc"]=datetime.now(timezone.utc).isoformat()
metadata["total_tokens"]=sum((r.get("usage") or {}).get("total_tokens",0) for r in metadata["runs"])
metadata["total_neurons"]=round(sum((r.get("usage") or {}).get("neurons",0) for r in metadata["runs"]),6)
est=[r.get("estimated_usd_before_free_allowance") for r in metadata["runs"]]
metadata["estimated_usd_before_free_allowance"]=round(sum(x for x in est if x is not None),8) if all(x is not None for x in est) else None
(OUT/"summary.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
print("=== C4.1_FINAL ===",flush=True)
print(json.dumps({
    "modes_completed":sum(r.get("api_success",False) for r in metadata["runs"]),
    "total_tokens":metadata["total_tokens"],
    "total_neurons":metadata["total_neurons"],
    "estimated_usd_before_free_allowance":metadata["estimated_usd_before_free_allowance"]
},ensure_ascii=False),flush=True)

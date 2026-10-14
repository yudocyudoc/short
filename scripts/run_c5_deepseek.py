#!/usr/bin/env python3
"""C5: library transfer test; same DeepSeek grammar B verbatim from C4.2."""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from c42_transport import separate
from c42_validator import evaluate

C4=ROOT/"experiments"/"c4"
C42=ROOT/"experiments"/"c4.2"
OUT=ROOT/"c5-cloudflare-results"
OUT.mkdir(exist_ok=True)
ACCOUNT=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
TOKEN=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
if not ACCOUNT or not TOKEN:
    raise SystemExit("Cloudflare account and token secrets are required")
MODEL="@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
URL=f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{MODEL}"
TEMP=0.1
MAX_TOKENS=3500
def read(path):return path.read_text(encoding="utf-8")
def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
scenario=read(C5/"scenario.md")
contract=read(C5/"prompts"/"contract.md")
build=read(C5/"prompts"/"common.md")
new_rule=read(ROOT/"experiments"/"c4.2"/"prompts"/"flow-coverage.md")
facts=json.loads(read(C5/"evaluation"/"facts.json"))
baseline="### Escenario\n"+scenario+"\n### Contrato\n"+contract+"\n\n### Instrucciones iniciales\n"+build
prompts={"A":baseline,"B":baseline+"\n\n### Reglas adicionales de cobertura de flujos\n"+new_rule}
metadata={
    "started_utc":datetime.now(timezone.utc).isoformat(),
    "model":MODEL,"temperature":TEMP,"max_tokens":MAX_TOKENS,
    "order":["A","B"],"max_calls":2,
    "prompt_sha256":{arm:sha(text) for arm,text in prompts.items()},
    "source_sha256":{"scenario":sha(scenario),"contract":sha(contract),
                     "build":sha(build),"extra_B":sha(new_rule)},
    "runs":[]
}

def response_value(wrapper):
    result=wrapper.get("result",wrapper)
    if isinstance(result,str):return result,{}
    if not isinstance(result,dict):
        return result,{}
    if "response" in result:
        return result["response"],result.get("usage",{})
    if isinstance(result.get("choices"),list) and result["choices"]:
        message=result["choices"][0].get("message",{})
        if isinstance(message,dict):
            return message.get("content"),result.get("usage",{})
    return None,result.get("usage",{})

def call(arm,prompt):
    body={"messages":[{"role":"user","content":prompt}],
          "stream":False,"temperature":TEMP,"max_tokens":MAX_TOKENS}
    (OUT/f"{arm}-request-no-secrets.json").write_text(
        json.dumps({"model":MODEL,"body":body},ensure_ascii=False,indent=2),encoding="utf-8")
    request=Request(URL,method="POST",headers={"Authorization":f"Bearer {TOKEN}",
            "Content-Type":"application/json"},data=json.dumps(body).encode("utf-8"))
    try:
        with urlopen(request,timeout=240) as reply:
            provider=json.load(reply)
    except HTTPError as e:
        message=e.read(2048).decode("utf-8","replace").replace(TOKEN,"***").replace(ACCOUNT,"***")
        return {"arm":arm,"status":"HTTP_ERROR","api_success":False,"http_code":e.code,"error":message[:400]}
    except (URLError,TimeoutError) as e:
        return {"arm":arm,"status":"TRANSPORT_ERROR","api_success":False,"error":e.__class__.__name__}
    (OUT/f"{arm}-provider.json").write_text(json.dumps(provider,ensure_ascii=False,indent=2),encoding="utf-8")
    if not provider.get("success",True):
        return {"arm":arm,"status":"PROVIDER_ERROR","api_success":False,"error":str(provider.get("errors",[]))[:400]}
    value,usage=response_value(provider)
    if isinstance(value,str):
        (OUT/f"{arm}-original.txt").write_text(value,encoding="utf-8")
    else:
        (OUT/f"{arm}-original.json").write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")
    obj,reasoning,transport,evaluated=validate_provider(value,facts)
    if reasoning is not None:
        (OUT/f"{arm}-reasoning.txt").write_text(reasoning,encoding="utf-8")
    if obj is not None:
        (OUT/f"{arm}-parsed-final.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    evaluated=evaluate(obj,facts)
    if not transport["ok"]:
        evaluated["status"]="FORMAT_REJECT"
    (OUT/f"{arm}-certificate.json").write_text(json.dumps({
        "transport":transport,"verification":evaluated
    },ensure_ascii=False,indent=2),encoding="utf-8")
    tin=usage.get("prompt_tokens")
    tout=usage.get("completion_tokens")
    estimate=round((0.497*tin+4.881*tout)/1e6,8) if type(tin)==int and type(tout)==int else None
    return {"arm":arm,"api_success":True,"transport":transport,
            "model_score":evaluated["score"],"p11_pass":evaluated["stock_flow_certificate"]["pass"],
            "status":evaluated["status"],
            "failed_gates":[g["id"] for g in evaluated["gates"] if not g["pass"]],
            "usage":usage,"estimated_usd_before_allowance":estimate}

for arm in ("A","B"):
    try:
        record=call(arm,prompts[arm])
    except Exception as e:
        record={"arm":arm,"status":"RUNNER_ERROR","api_success":False,
                "error":(e.__class__.__name__+":"+str(e)).replace(TOKEN,"***").replace(ACCOUNT,"***")[:300]}
    metadata["runs"].append(record)
    print("=== C5 "+arm+" ===",flush=True)
    print(json.dumps(record,ensure_ascii=False),flush=True)
metadata["finished_utc"]=datetime.now(timezone.utc).isoformat()
metadata["total_tokens"]=sum((x.get("usage") or {}).get("total_tokens",0) for x in metadata["runs"])
metadata["total_neurons"]=round(sum((x.get("usage") or {}).get("neurons",0) for x in metadata["runs"]),6)
money=[x.get("estimated_usd_before_allowance") for x in metadata["runs"]]
metadata["estimated_usd_before_allowance"]=round(sum(x for x in money if x is not None),8) if all(x is not None for x in money) else None
(OUT/"summary.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
print("=== C5_FINAL ===",flush=True)
print(json.dumps({"calls":len(metadata["runs"]),
                  "total_tokens":metadata["total_tokens"],"total_neurons":metadata["total_neurons"],
                  "usd_estimate":metadata["estimated_usd_before_allowance"]},ensure_ascii=False),flush=True)
if not all(x.get("api_success") for x in metadata["runs"]):
    sys.exit(2)

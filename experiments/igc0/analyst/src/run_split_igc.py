#!/usr/bin/env python3
"""IGC0 M01 v3: DeepSeek I/G -> deterministic gate -> DeepSeek contrast.

No retries, no repairs, no oracle or aggregate simulation; maximum 2 API calls.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from datetime import datetime,timezone
from prepare import write,sha
from run_llm import separate,diagram,MODEL
from igc_split_gate import graph_gate,contrast_gate

def sha_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def response_kind(provider):
    result=provider.get("result",provider)
    if isinstance(result,str):
        return result,{}
    if isinstance(result,dict):
        usage=result.get("usage",{})
        if "response" in result:
            return result["response"],usage
        choices=result.get("choices",[])
        if isinstance(choices,list) and choices:
            return choices[0]["message"].get("content"),usage
    return None,{}

def request_stage(tag,prompt,payload,out,account,token):
    stage=out/tag
    stage.mkdir(parents=True,exist_ok=True)
    body={"messages":[
        {"role":"system","content":prompt},
        {"role":"user","content":json.dumps(payload,ensure_ascii=False,separators=(",",":"))}],
        "temperature":0.1,"max_tokens":4500,"stream":False}
    serialized=json.dumps(body,ensure_ascii=False,separators=(",",":"))
    write(stage/"request_manifest.json",{
        "stage":tag,"model":MODEL,"temperature":0.1,"max_tokens":4500,
        "request_sha256":sha_text(serialized),
        "prompt_sha256":sha_text(prompt),
        "input_sha256":sha(payload),
        "first_or_second_of_two":tag,
        "requests_executed_by_function":1})
    (stage/"prompt_used.md").write_text(prompt,encoding="utf-8")
    url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
    request=Request(url,method="POST",headers={
        "Authorization":f"Bearer {token}","Content-Type":"application/json"},
        data=serialized.encode("utf-8"))
    try:
        with urlopen(request,timeout=240) as reply:
            provider=json.load(reply)
    except (HTTPError,URLError,TimeoutError) as e:
        code=e.code if isinstance(e,HTTPError) else None
        write(stage/"transport_error.json",{"error_type":type(e).__name__,"http_status":code,
                                            "retry_count":0})
        return None,{"api_success":False,"type":type(e).__name__,"http_status":code}
    write(stage/"provider_response.json",provider)
    if not provider.get("success",True):
        write(stage/"provider_error.json",{"success":False,
                                          "errors":provider.get("errors",[])})
        return None,{"api_success":False,"type":"PROVIDER_ERROR"}
    value,usage=response_kind(provider)
    if isinstance(value,str):
        (stage/"raw_response.txt").write_text(value,encoding="utf-8")
    else:
        write(stage/"raw_response.json",value)
    obj,reasoning,kind=separate(value)
    if reasoning is not None:
        (stage/"reasoning.txt").write_text(reasoning,encoding="utf-8")
    if obj is not None:
        write(stage/"parsed_final.json",obj)
    write(stage/"usage.json",{"provider":MODEL,"usage":usage,"format":kind,
         "api_success":True,"estimated_usd_before_free_allowance":
            round((usage["prompt_tokens"]*0.497+usage["completion_tokens"]*4.881)/1_000_000,8)
            if type(usage.get("prompt_tokens"))==int and type(usage.get("completion_tokens"))==int else None})
    return obj,{"api_success":True,"format":kind,"usage":usage}

def execute(packet,out,account,token,graph_prompt,contrast_prompt):
    out.mkdir(parents=True,exist_ok=True)
    meta={"case_id":packet["case_id"],"input_sha256":sha(packet),"model":MODEL,
          "started_utc":datetime.now(timezone.utc).isoformat(),
          "max_model_calls":2,"model_calls_attempted":0,
          "oracle_loaded":False,"aggregate_sd_loaded":False,"automatic_retries":0,
          "projection_permitted":False}
    # FIRST call
    meta["model_calls_attempted"]=1
    graph,result=request_stage("IG",graph_prompt,packet,out,account,token)
    meta["IG_transport"]=result
    if graph is None:
        meta["IG_accept"]=False
        meta["C_status"]="SKIPPED_IG_REJECT"
        meta["status"]="FORMAT_OR_PROVIDER_REJECT"
    else:
        checked=graph_gate(graph,packet)
        write(out/"IG"/"graph_validation.json",checked)
        meta["IG_accept"]=checked["accepted"]
        meta["IG_graph_sha256"]=checked["graph_sha256"]
        meta["IG_counts"]={"stocks":checked["stock_count"],"pipes":checked["pipe_count"]}
        if checked["accepted"]:
            (out/"IG"/"diagram.mmd").write_text(diagram(graph),encoding="utf-8")
            meta["model_calls_attempted"]=2
            # SECOND call: only the accepted graph and the same public evidence
            contrast,second=request_stage("C",contrast_prompt,{
                "evidence":packet,"accepted_graph":graph,
                "graph_sha256":checked["graph_sha256"]
            },out,account,token)
            meta["C_transport"]=second
            if contrast is None:
                meta["C_status"]="FORMAT_OR_PROVIDER_REJECT"
                meta["status"]="CONTRAST_REJECT"
            else:
                judgement=contrast_gate(contrast,graph,packet)
                write(out/"C"/"contrast_validation.json",judgement)
                meta["C_status"]="ACCEPT" if judgement["accepted"] else "REJECT"
                meta["status"]="IGC_CONTRACT_ACCEPT" if judgement["accepted"] else "CONTRAST_REJECT"
                if judgement["accepted"]:
                    # No changes to graph; the separate hash links C back to IG.
                    combined={**graph,**{k:v for k,v in contrast.items() if k!="graph_sha256"}}
                    write(out/"combined_igc_model.json",combined)
        else:
            meta["C_status"]="SKIPPED_IG_REJECT"
            meta["status"]="IG_REJECT"
    meta["finished_utc"]=datetime.now(timezone.utc).isoformat()
    meta["calls_reported"]=meta["model_calls_attempted"]
    write(out/"summary.json",meta)
    print("IGC0_M01_SPLIT_SUMMARY",json.dumps(meta,ensure_ascii=False),flush=True)
    # Deliberately exit 0 for model rejection; the verdict is experimental data.
    return meta

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--inputs",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--ig-prompt",type=Path,required=True)
    ap.add_argument("--contrast-prompt",type=Path,required=True)
    ap.add_argument("--case",choices=["M01"],default="M01")
    args=ap.parse_args()
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token:
        raise SystemExit("Cloudflare account/token secrets are required; no API calls made")
    packet=json.loads((args.inputs/(args.case+".json")).read_text(encoding="utf-8"))
    assert packet["case_id"]=="M01"
    assert packet["epistemic"]["counterfactual_without_model"]=="DESCONOCIDO"
    igp=args.ig_prompt.read_text(encoding="utf-8")
    cp=args.contrast_prompt.read_text(encoding="utf-8")
    assert "informational_links" in igp and "graph_sha256" in cp
    execute(packet,args.out/"M01",account,token,igp,cp)

if __name__=="__main__":
    main()

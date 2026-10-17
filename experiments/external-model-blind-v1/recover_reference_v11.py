#!/usr/bin/env python3
"""v1.1 prospective FORMAT recovery of failed blind reference generation.

Reuses exactly 16 original valid Qwen cases from run 38995455018, externally
frozen before any Llama inference. Does not change Qwen facts, prompts for
tested Llama, scoring, catalog or make new generated cases.
"""
from __future__ import annotations
import argparse,hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import run_blind as orig

PRIOR_SOURCE_SHA256="b296c42fe129e59bffa158a2bec771b36d39e21e5ddbc7424c0734ac5cf122c9"
PRIOR_RUN_ID=38995455018
PRIOR_ARTIFACT_ID=12086714733

def run(out,original_input):
    orig.verify_frozen()
    data=original_input.read_bytes()
    if hashlib.sha256(data).hexdigest()!=PRIOR_SOURCE_SHA256:
        raise SystemExit("REFUSE_UNVERIFIED_PRE_LLAM A_QWEN_CORPUS".replace(" ",""))
    cases=json.loads(data)["cases"]
    if len(cases)!=16 or len({c["id"] for c in cases})!=16:
        raise SystemExit("SOURCE_CORPUS_DRIFT")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token:raise SystemExit("CLOUDFLARE_SECRETS_MISSING")
    root=out/"reference"
    root.mkdir(parents=True,exist_ok=True)
    orig.save(root/"generated_cases_from_previous_run.json",{"cases":cases})
    states={};entries=[];gold={}
    model=orig.CFG["reviewer_model"]
    for case in cases:
        cid=case["id"];msgs=orig.review_messages(case)
        # Cloudflare officially supports turning thinking off on GLM.
        body={"messages":msgs,"stream":False,"temperature":0,
              "max_tokens":1600,"reasoning_effort":None,
              "chat_template_kwargs":{"enable_thinking":False}}
        folder=root/"reviewer"/cid
        orig.save(folder/"request_without_secrets.json",{"model":model,"body":body})
        entry={"id":cid,"model":model,"status":"REQUEST_PREPARED",
               "input_sha256":orig.sha(json.dumps(msgs,ensure_ascii=False))}
        req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+model,
          method="POST",headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},
          data=json.dumps(body,ensure_ascii=False).encode("utf-8"))
        try:
            with urlopen(req,timeout=150) as resp:provider=json.load(resp)
            orig.save(folder/"provider_original.json",provider)
            text=orig.old_prompt.extract(provider)
            (folder/"original.txt").write_text(text,encoding="utf-8")
            entry.update({"status":"RECEIVED","raw_sha256":orig.sha(text),"length":len(text)})
            reference=orig.parse_reference(case,text)
            if reference is None:
                states[cid]="INDETERMINATE_BY_REVIEWER"
            else:
                gold[cid]=reference
                states[cid]="LABELLED"
                orig.save(folder/"parsed_reference.json",reference)
        except HTTPError as e:states[cid]="HTTP_ERROR:"+str(e.code)
        except (URLError,TimeoutError) as e:states[cid]="TRANSPORT_ERROR:"+type(e).__name__
        except (ValueError,TypeError,KeyError) as e:states[cid]="INVALID_REFERENCE:"+str(e)
        entries.append(entry)
        print("RECOVERY_GL M_REFERENCE".replace(" ",""),json.dumps({"id":cid,"status":states[cid]}),flush=True)
        orig.save(root/"recovery_progress.json",{"entries":entries,"case_status":states})
    scored=[case for case in cases if case["id"] in gold]
    orig.save(root/"scored_cases.json",{"cases":scored})
    orig.save(root/"proxy_reference.json",{"cases":gold,
       "warning":"GLM labels are automatic proxy reference, NOT human-established causal truth."})
    status={"version":"PROSPECTIVE_TECHNICAL_RECOVERY_V1_1",
        "source_run":PRIOR_RUN_ID,"source_artifact":PRIOR_ARTIFACT_ID,
        "source_sha256":PRIOR_SOURCE_SHA256,
        "invalid_original_qwen_cases_excluded":8,
        "reused_original_valid_qwen_cases":16,
        "case_states":states,"n_labelled":len(scored),
        "n_excluded_from_original_24":24-len(scored),
        "reviewer_config":{"model":model,"enable_thinking":False,"max_tokens":1600},
        "gold_sha256":orig.sha(json.dumps(gold,sort_keys=True)),
        "completed_before_llama":True,
        "saved_utc":datetime.now(timezone.utc).isoformat()}
    orig.save(root/"status.json",status)
    print("RECOVERY_FROZEN_REFERENCE",json.dumps({
       "valid":len(scored),"excluded":24-len(scored),"gold_sha256":status["gold_sha256"]}),flush=True)
    if len(scored)<12:raise SystemExit("INSUFFICIENT_VALID_LABELS_STOP_BEFORE_LLAMA")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--original-input",required=True,type=Path)
    a=p.parse_args();run(a.out,a.original_input)

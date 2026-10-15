#!/usr/bin/env python3
"""Single new IGC0 M01 v2 DeepSeek call; unchanged underlying Cloudflare transport.

Original v1 artifacts are untouched. v2 inputs are public-only; oracle inaccessible.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError,URLError
import run_llm
from semantic_audit_v2 import audit_v2
from prepare import write,sha

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--inputs",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--case",default="M01",choices=["M01"])
    parser.add_argument("--prompt",type=Path,required=True)
    args=parser.parse_args()
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if not account or not token:
        raise SystemExit("Cloudflare secrets missing; no inference performed")
    packet=json.loads((args.inputs/(args.case+".json")).read_text(encoding="utf-8"))
    assert packet["case_id"]=="M01"
    prompt=args.prompt.read_text(encoding="utf-8")
    assert "mechanism_checks" in prompt and "informational_links" in prompt
    assert packet["epistemic"]["counterfactual_without_model"]=="DESCONOCIDO"
    run_llm.PROMPT_SYSTEM=prompt
    out=args.out/args.case
    out.mkdir(parents=True,exist_ok=True)
    (out/"prompt_used.md").write_text(prompt,encoding="utf-8")
    try:
        # One model call. This saves raw response, reasoning, proposal and old validator.
        cid,tech_ok,format_kind=run_llm.one(packet,args.out,account,token)
    except (HTTPError,URLError,TimeoutError) as e:
        write(out/"error.json",{"case_id":args.case,"error_type":type(e).__name__,
                                 "max_attempts":1,"automatic_retry":False})
        print("IGC0_M01_V2_API_ERROR",type(e).__name__,flush=True)
        raise
    model_path=out/"proposed_model.json"
    if model_path.exists():
        model=json.loads(model_path.read_text(encoding="utf-8"))
        semantic=audit_v2(model,packet)
    else:
        semantic={"accepted":False,"issues":[{"code":"FORMAT_REJECT","where":"raw_response",
            "detail":"No parseable typed JSON generated"}],"validator":"IGC0_SEMANTIC_V2"}
    write(out/"semantic_v2.json",semantic)
    combined={"case_id":cid,"model":"@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
              "format":format_kind,"original_validator_accepted":tech_ok,
              "v2_semantic_accepted":semantic["accepted"],
              "igc_contract_accepted":bool(tech_ok and semantic["accepted"]),
              "original_validator_not_causal_proof":True,
              "data_origin":"public evidence only","oracle_loaded":False,
              "projection_permitted":False,
              "prompt_sha256":hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
              "input_sha256":sha(packet),
              "attempts":1,"revisions":0}
    write(out/"adjudication_v2.json",combined)
    print("IGC0_M01_V2_RESULT",json.dumps(combined,ensure_ascii=False),flush=True)
    print("IGC0_M01_V2_SEMANTIC",json.dumps(semantic,ensure_ascii=False),flush=True)
    # The LLM/model's semantic failure is an experimental outcome, not a broken runner.
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Replay the exact first real Llama response archived by prior failed run.
No LLM call; proves the observed failure was format handling, not graph content.
"""
import argparse,hashlib,json
from pathlib import Path
from compose import validate,render
from run_cycle import parse_proposal_text

ORIGINAL_SHA256="231ee808fdb72dff8ba643bb8de58716a77ba5d49e90c4059950f46342ee44ee"
ORIGINAL_RUN="38997693854"
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--model",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    b=a.original.read_bytes()
    if hashlib.sha256(b).hexdigest()!=ORIGINAL_SHA256:
        raise SystemExit("ARCHIVED_LLAMA_RESPONSE_SHA_DRIFT")
    raw=b.decode("utf-8")
    graph=parse_proposal_text(raw)
    result=validate(graph)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    report={"source_run":ORIGINAL_RUN,"source_sha256":ORIGINAL_SHA256,
      "model":"Llama 3.3 70B Cloudflare","new_model_calls":0,
      "parser_change":"only unwrap exactly one JSON markdown fence",
      "structural_adjudication":result,
      "retrospective_replay_not_new_llm_trial":True}
    if result["structure_accepted"]:
        a.model.write_text(render(graph),encoding="utf-8")
        report["model_source_sha256"]=hashlib.sha256(a.model.read_bytes()).hexdigest()
    a.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("FIRST_LLAMA_ORIGINAL_REPLAY",json.dumps(report),flush=True)
    if not result["structure_accepted"]:raise SystemExit("FIRST_ORIGINAL_STRUCTURE_REJECTED")
if __name__=="__main__":main()

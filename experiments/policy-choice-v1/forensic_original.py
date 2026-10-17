#!/usr/bin/env python3
"""Forensic, explicitly POST-HOC separation of policy intent from AST admission.

Reads original archived Llama replies. NEVER changes original strict scorer,
labels, prompts or validates Modelica. 'Intent' is not a PASS for the gate.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from run_study import parse,label
import compose
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    gold=compose.read("evaluation_gold.json")["cases"]
    findings=[]
    for case in compose.read("cases.json")["cases"]:
        cid=case["id"];expected=gold[cid]["policy"] or gold[cid]["status"]
        responses=[]
        for i in (1,2):
            file=a.archive/"llama_real"/cid/("attempt_"+str(i))/"original.txt"
            if file.exists():
                raw=file.read_text(encoding="utf-8")
                responses.append({"attempt":i,"raw_sha256":hashlib.sha256(raw.encode()).hexdigest(),
                   "proposal":parse(raw)})
        if not responses:raise ValueError("MISSING_ORIGINAL_RESPONSE:"+cid)
        first=responses[0]["proposal"]
        intended=label(first)
        facts={f["id"]:f["text"] for f in case["facts"]}
        def literal_cited(q):
            if isinstance(q,str):
                return any(len(q.strip())>=24 and q in t for t in facts.values())
            if isinstance(q,dict):
                return isinstance(q.get("quote"),str) and isinstance(q.get("fact_id"),str) and q.get("quote") in facts.get(q.get("fact_id"),"")
            return False
        support=first.get("support",[])
        rival=first.get("counterevidence",[])
        findings.append({"case_id":cid,"gold":expected,
          "first_original_intent":intended,"intent_matches_gold":intended==expected,
          "note":"Intent inferred from raw selected decision/policy only; AST and evidence not accepted by strict gate",
          "support": [{"type":type(s).__name__,"literal_verifiable":literal_cited(s)} for s in support] if isinstance(support,list) else [],
          "rival_rejections":[{"type":type(s).__name__,"literal_verifiable":literal_cited(s)} for s in rival] if isinstance(rival,list) else [],
          "attempt_hashes":[{"attempt":x["attempt"],"sha256":x["raw_sha256"]} for x in responses]})
    report={"analysis":"POST_HOC_RAW_POLICY_INTENT_NOT_EXECUTABLE_GRAPH",
      "source_run":"39001963771","source_artifact_id":12089821237,
      "n":len(findings),"raw_intent_matches_gold":sum(x["intent_matches_gold"] for x in findings),
      "policy_positive_count":8,
      "correct_positive_intent":sum(x["intent_matches_gold"] for x in findings if x["gold"] in ("MTO","MTS")),
      "cases":findings,
      "caution":"Does NOT replace the preregistered strict 3/12: evidence and graph schemas were rejected. Interpretation was developed after inspecting outputs. This is diagnostic only, not new blinded statistical evaluation."}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("POST_HOC_ORIGINAL_POLICY_INTENT",json.dumps({"intent":report["raw_intent_matches_gold"],"n":report["n"],"positive":report["correct_positive_intent"]}),flush=True)
if __name__=="__main__":main()

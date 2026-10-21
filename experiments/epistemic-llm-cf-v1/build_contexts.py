#!/usr/bin/env python3
"""Build paired contexts and cross-check canonical support labels two ways."""
import argparse, hashlib, itertools, json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def minimal(envs):
    envs=set(envs)
    return {e for e in envs if not any(other < e for other in envs)}

def canonical(labels,nodes):
    return {node:[sorted(e) for e in sorted(labels.get(node,set()),key=lambda x:(len(x),sorted(x)))] for node in sorted(nodes)}

def atms_labels(case,nogoods):
    labels={a["id"]:{frozenset({a["id"]})} for a in case["assumptions"]}
    forbidden=[frozenset(x) for x in nogoods]
    for rule in case["justifications"]:
        choices=[labels[a] for a in rule["antecedents"]]
        envs={frozenset().union(*combo) for combo in itertools.product(*choices)}
        valid={env for env in envs if not any(g<=env for g in forbidden)}
        labels.setdefault(rule["conclusion"],set()).update(valid)
    return labels

def or_and_closure(case,nogoods):
    labels={a["id"]:{frozenset({a["id"]})} for a in case["assumptions"]}
    forbidden=[frozenset(x) for x in nogoods]
    changed=True
    while changed:
        changed=False
        for rule in case["justifications"]:
            choices=[labels.get(a,set()) for a in rule["antecedents"]]
            if any(not values for values in choices): continue
            derived={frozenset().union(*combo) for combo in itertools.product(*choices)}
            derived={e for e in derived if not any(g<=e for g in forbidden)}
            node=rule["conclusion"]
            updated=minimal(labels.get(node,set())|derived)
            if updated!=labels.get(node,set()):
                labels[node]=updated
                changed=True
    return labels

def labels_for_revision(case,invalidated):
    nogoods=[[item] for item in invalidated]
    nodes=[h["id"] for h in case["hypotheses"]]
    atms=canonical(atms_labels(case,nogoods),nodes)
    closure=canonical(or_and_closure(case,nogoods),nodes)
    if atms!=closure: raise ValueError("ATMS_OR_AND_CONTEXT_MISMATCH")
    return atms

def build(case):
    before=labels_for_revision(case,[])
    invalidated=case["revisions"][-1]["invalidates"]
    after=labels_for_revision(case,invalidated)
    source={"case_id":case["case_id"],"question":case["question"],"records":case["records"],
      "claims":case["claims"],"hypotheses":case["hypotheses"],"assumptions":case["assumptions"],
      "revisions":case["revisions"],"tasks":case["tasks"],
      "sd_discrimination_context":case["sd_discrimination_context"],"no_empirical_or_causal_claim":True}
    statuses={node:("supported" if envs else "unsupported") for node,envs in after.items()}
    traces={}
    for rule in case["justifications"]:
        traces.setdefault(rule["conclusion"],[]).append({
          "justification_id":rule["id"],"antecedents":rule["antecedents"],"source_ids":rule["source_ids"],
          "status":"invalidated" if any(set(g)<=set(rule["antecedents"]) for g in case["nogoods"]) else "survives"})
    return {
      "A":{"arm":"A_documental",**source},
      "B":{"arm":"B_booleano",**source,"current_hypothesis_status":statuses},
      "C":{"arm":"C_epistemologico",**source,"logical_context":{
        "engine_equivalence":"ATMS_AND_OR_AND_EXACT","before_review_minimal_support_environments":before,
        "current_minimal_support_environments":after,"current_hypothesis_status":statuses,
        "justification_trace":traces,"nogoods":case["nogoods"],
        "canonical_label_semantics":"Each environment is AND; alternative environments are OR."}}
    }

def write_contexts(case_path,out_dir):
    case=json.loads(case_path.read_text(encoding="utf-8"))
    contexts=build(case); out_dir.mkdir(parents=True,exist_ok=True); hashes={}
    for arm,context in contexts.items():
        payload=json.dumps(context,ensure_ascii=False,indent=2)+"\n"
        (out_dir/f"context-{arm}.json").write_text(payload,encoding="utf-8")
        hashes[arm]=hashlib.sha256(payload.encode("utf-8")).hexdigest()
    task={"common_instructions":(HERE/"prompts/common.md").read_text(encoding="utf-8"),"tasks":case["tasks"]}
    (out_dir/"tasks.json").write_text(json.dumps(task,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    result={"case_id":case["case_id"],"status":"PREPARED_NO_INFERENCE","atms_or_and_equivalence":"PASS",
      "context_sha256":hashes,"calls_planned":9,"calls_made":0,"empirical_or_causal_claim":False}
    (out_dir/"preparation-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("--case",type=Path,default=HERE/"case.json"); p.add_argument("--out",type=Path,required=True)
    a=p.parse_args(); print(json.dumps(write_contexts(a.case,a.out),ensure_ascii=False))
if __name__=="__main__": main()

#!/usr/bin/env python3
"""Build paired EPI-01 contexts and compare the pinned IGC AtmsProbe to OR/AND."""
import argparse, hashlib, importlib.util, itertools, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROBE_PATH=HERE/"references"/"f0_atms_probe.py"
spec=importlib.util.spec_from_file_location("igc_f0_atms_probe",PROBE_PATH)
probe=importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
AtmsProbe=probe.AtmsProbe
ATMS_SOURCE_BLOB="659e9dfe463daf4a03144c8d55622c9eeffca79a"

def minimal(envs):
    envs=set(envs)
    return {e for e in envs if not any(other < e for other in envs)}

def canonical(labels,nodes):
    return {node:[sorted(e) for e in sorted(labels.get(node,set()),key=lambda x:(len(x),sorted(x)))] for node in sorted(nodes)}

def authentic_atms_labels(case,nogoods):
    engine=AtmsProbe()
    for assumption in case["assumptions"]:
        engine.assume(assumption["id"])
    for rule in case["justifications"]:
        engine.justify(tuple(rule["antecedents"]),rule["conclusion"])
    for nogood in nogoods:
        engine.add_nogood(frozenset(nogood))
    nodes=[h["id"] for h in case["hypotheses"]]
    return canonical(engine.labels,nodes)

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
    nodes=[h["id"] for h in case["hypotheses"]]
    return canonical(labels,nodes)

def labels_for_revision(case,nogoods):
    atms=authentic_atms_labels(case,nogoods)
    closure=or_and_closure(case,nogoods)
    if atms!=closure: raise ValueError("PINNED_IGC_ATMS_OR_AND_MISMATCH")
    return atms

def build(case):
    before=labels_for_revision(case,[])
    invalidated=case["revisions"][-1]["invalidates"]
    after=labels_for_revision(case,[[item] for item in invalidated])
    source={"case_id":case["case_id"],"synthetic":case["synthetic"],"question":case["question"],
      "records":case["records"],"claims":case["claims"],"hypotheses":case["hypotheses"],
      "assumptions":case["assumptions"],"justifications":case["justifications"],
      "revisions":case["revisions"],"tasks":case["tasks"],
      "sd_discrimination_context":case["sd_discrimination_context"],
      "no_empirical_or_causal_claim":True}
    statuses={node:("supported" if envs else "unsupported") for node,envs in after.items()}
    traces={}
    for rule in case["justifications"]:
        traces.setdefault(rule["conclusion"],[]).append({
          "justification_id":rule["id"],"antecedents":rule["antecedents"],"source_ids":rule["source_ids"],
          "status":"invalidated" if any(x in rule["antecedents"] for x in invalidated) else "survives"})
    equivalence={"result":"EXACT_FOR_EPI01_FIXTURE","reference":"IGC_F0_AtmsProbe",
      "reference_source_blob":ATMS_SOURCE_BLOB,"comparator":"local_OR_AND_least_fixed_point"}
    return {
      "A":{"arm":"A_documental",**source},
      "B":{"arm":"B_booleano",**source,"current_hypothesis_status":statuses},
      "C":{"arm":"C_epistemologico",**source,"logical_context":{
        "engine_equivalence":equivalence,"before_review_minimal_support_environments":before,
        "current_minimal_support_environments":after,"current_hypothesis_status":statuses,
        "justification_trace":traces,"nogoods":[[x] for x in invalidated],
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
    result={"case_id":case["case_id"],"status":"PREPARED_NO_INFERENCE",
      "atms_reference":"PINNED_IGC_F0_AtmsProbe","atms_or_and_equivalence":"EXACT_FOR_EPI01_FIXTURE",
      "atms_source_blob":ATMS_SOURCE_BLOB,"context_sha256":hashes,
      "calls_planned":9,"calls_made":0,"empirical_or_causal_claim":False}
    (out_dir/"preparation-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("--case",type=Path,default=HERE/"case.json"); p.add_argument("--out",type=Path,required=True)
    a=p.parse_args(); print(json.dumps(write_contexts(a.case,a.out),ensure_ascii=False))
if __name__=="__main__": main()

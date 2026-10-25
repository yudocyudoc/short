#!/usr/bin/env python3
"""EPI-02: paired contexts from pinned IGC F0 probe and an independent OR/AND closure.
Only historical revision states are sent to the LLM. Counterfactual outcomes are NOT.
"""
from __future__ import annotations
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE_PATH = HERE / "references" / "f0_atms_probe.py"
PROBE_BLOB = "659e9dfe463daf4a03144c8d55622c9eeffca79a"
spec = importlib.util.spec_from_file_location("igc_epi02_atms_probe", PROBE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
AtmsProbe = module.AtmsProbe

def canonical(raw, ids):
    return {k: [sorted(e) for e in sorted(raw.get(k, set()), key=lambda x:(len(x),sorted(x)))]
            for k in sorted(ids)}

def atms(case, invalidated):
    engine = AtmsProbe()
    for a in case["assumptions"]:
        engine.assume(a["id"])
    for rule in case["rules"]:
        engine.justify(tuple(rule["antecedents"]), rule["consequent"])
    for assumption in invalidated:
        engine.add_nogood(frozenset({assumption}))
    return canonical(engine.labels, [h["id"] for h in case["hypotheses"]])

def or_and(case, invalidated):
    assumptions = {a["id"] for a in case["assumptions"]}
    forbidden = set(invalidated)
    labels = {a: {frozenset({a})} if a not in forbidden else set() for a in assumptions}
    changed = True
    while changed:
        changed = False
        for rule in case["rules"]:
            choices = [labels.get(a, set()) for a in rule["antecedents"]]
            if any(not v for v in choices):
                continue
            products = {frozenset().union(*parts) for parts in itertools.product(*choices)}
            union = labels.get(rule["consequent"], set()) | products
            mins = {e for e in union if not any(other < e for other in union)}
            if mins != labels.get(rule["consequent"], set()):
                labels[rule["consequent"]] = mins
                changed = True
    return canonical(labels, [h["id"] for h in case["hypotheses"]])

def calculate(case, invalidated):
    a, b = atms(case, invalidated), or_and(case, invalidated)
    if a != b:
        raise AssertionError(f"IGC_ATMS_OR_AND_MISMATCH for {case['id']}")
    return a

def status(labels):
    return {hyp: ("SUPPORTED" if env else "UNSUPPORTED") for hyp, env in labels.items()}

def validate_case(case):
    a = {x["id"] for x in case["assumptions"]}
    h = {x["id"] for x in case["hypotheses"]}
    r = {x["id"] for x in case["records"]}
    nodes = a | h | {rule["consequent"] for rule in case["rules"]}
    assert len(a) == len(case["assumptions"]) and len(h) == 2
    assert all(n not in h for n in a)
    assert len(case["revisions"]) == 3 and [x["id"] for x in case["revisions"]] == ["R0","R1","R2"]
    for rule in case["rules"]:
        assert all(x in nodes for x in rule["antecedents"])
        assert set(rule["source_ids"]) <= r
    previous = set()
    for rev in case["revisions"]:
        current = set(rev["invalidated"])
        assert previous <= current <= a
        previous = current
    assert set(case["counterfactual"]["additional_invalidated"]) <= a
    assert not set(case["counterfactual"]["additional_invalidated"]) <= previous

def build(case):
    validate_case(case)
    revision_labels = {rev["id"]: calculate(case, rev["invalidated"]) for rev in case["revisions"]}
    revision_states = {rev: status(labels) for rev, labels in revision_labels.items()}
    source = {key: case[key] for key in ("id","question","hypotheses","records","assumptions","rules","revisions","counterfactual")}
    source["synthetic"] = True
    source["scope"] = "Conditional logical support is neither truth nor causality."
    return {
        "B": {"condition":"BOOLEAN","dossier":source, "status_by_revision":revision_states},
        "C": {"condition":"EPISTEMIC","dossier":source, "status_by_revision":revision_states,
              "minimal_support_by_revision":revision_labels,
              "label_semantics":"Within each environment AND; across environments OR. Sets are minimal.",
              "engine_reference":{"name":"IGC_F0_AtmsProbe","blob":PROBE_BLOB,
                                  "comparison":"EXACT_FOR_EPI02_FIXTURES_ONLY"}}
    }

def sha(content):
    return hashlib.sha256(content).hexdigest()

def prepare(out_dir, cases_path=HERE/"cases.json"):
    data = json.loads(cases_path.read_text(encoding="utf-8"))
    assert data["synthetic"] is True and data["empirical_or_causal_claim"] is False
    assert len(data["cases"]) == 2
    out_dir.mkdir(parents=True,exist_ok=True)
    hashes = {}
    for case in data["cases"]:
        for arm, context in build(case).items():
            target = out_dir/f"context-{case['id']}-{arm}.json"
            content = json.dumps(context,ensure_ascii=False,indent=2)+"\n"
            target.write_text(content,encoding="utf-8")
            hashes[target.name] = sha(content.encode("utf-8"))
    report = {"status":"PREPARED_NO_INFERENCE","calls_planned":24,"calls_made":0,
              "cases":len(data["cases"]),"arms":["B","C"],"repetitions":3,
              "model":"@cf/zai-org/glm-4.7-flash","reference_blob":PROBE_BLOB,
              "parity":"EXACT_FOR_EPI02_FIXTURES_ONLY",
              "case_sha256":sha(cases_path.read_bytes()),"context_sha256":hashes}
    (out_dir/"preparation-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

if __name__ == "__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(prepare(args.out),ensure_ascii=False))

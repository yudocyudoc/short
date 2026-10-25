#!/usr/bin/env python3
"""EPI-06 independent exhaustive and antichain oracle; no model scores enter."""
from __future__ import annotations
import itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FIXTURES=ROOT/"fixtures"/"cases.json"
GOLD=ROOT/"evaluation"/"gold.json"
STATES=("BOTH","NEITHER","ONLY_H1","ONLY_H2")

def encode(H1,H2):
    return "BOTH" if H1 and H2 else "ONLY_H1" if H1 else "ONLY_H2" if H2 else "NEITHER"

def _ground(case):
    assumptions={a["id"] for a in case["assumptions"]}
    assert len(assumptions)==len(case["assumptions"])
    assert set(case["revisions"][-1]["revoked"])<=assumptions
    assert case["target_revision"]==case["revisions"][-1]["id"]
    active=assumptions-set(case["revisions"][-1]["revoked"])
    return assumptions,active

def enumerate_support(case):
    assumptions,active=_ground(case)
    supported=set()
    for size in range(len(active)+1):
        for group in itertools.combinations(sorted(active),size):
            subset=set(group)
            if any(set(ng)<=subset for ng in case["nogoods"]):
                continue
            closure=set(subset)
            for _ in range(len(case["rules"])+2):
                new={r["consequent"] for r in case["rules"]
                     if set(r["antecedents"])<=closure}
                if new<=closure:
                    break
                closure |= new
            supported |= closure&{"H1","H2"}
    return encode("H1" in supported,"H2" in supported)

def antichain_support(case):
    assumptions,active=_ground(case)
    labels={a:({frozenset([a])} if a in active else set()) for a in assumptions}
    for _ in range((len(assumptions)+1)*(len(case["rules"])+1)):
        changed=False
        for rule in case["rules"]:
            terms=[labels.get(a,set()) for a in rule["antecedents"]]
            if not terms or any(not t for t in terms):continue
            product={frozenset().union(*v) for v in itertools.product(*terms)}
            product={env for env in product if not any(set(ng)<=env for ng in case["nogoods"])}
            seen=labels.get(rule["consequent"],set())|product
            minimal={x for x in seen if not any(y<x for y in seen)}
            if minimal!=labels.get(rule["consequent"],set()):
                labels[rule["consequent"]]=minimal
                changed=True
        if not changed:break
    else:raise AssertionError("Provenance fixed point did not converge")
    return encode(bool(labels.get("H1")),bool(labels.get("H2")))

def validate():
    data=json.loads(FIXTURES.read_text(encoding="utf-8"))
    gold=json.loads(GOLD.read_text(encoding="utf-8"))
    assert gold["locked_before_provider"] is True
    cases=data["cases"]
    assert len(cases)==20 and len({c["id"] for c in cases})==20
    assert sum(gold["case_class"][c["id"]]=="NEITHER" for c in cases)==8
    from collections import Counter
    assert Counter(gold["case_class"].values())=={"BOTH":4,"ONLY_H1":4,"ONLY_H2":4,"NEITHER":8}
    for case in cases:
        assert case["id"] in gold["case_class"]
        a,b=enumerate_support(case),antichain_support(case)
        if a!=b or a!=gold["case_class"][case["id"]]:
            raise AssertionError(f"GOLD_DISAGREEMENT:{case['id']}:{a}:{b}")
    return cases,gold

if __name__=="__main__":
    cases,gold=validate()
    print(json.dumps({"cases":len(cases),"validated":True,"inference":0}))

#!/usr/bin/env python3
"""Deterministic reference, independent of Clef/GLM/Clairic. No ML inference.

Two independent implementations check logical support: exhaustive compatible
assumption subsets and antichain provenance closure. Numeric calculations use Decimal.
"""
from __future__ import annotations
import itertools
from decimal import Decimal
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
STATES=("BOTH","ONLY_H1","ONLY_H2","NEITHER")

def _case_nodes(case):
    assumptions={x["id"] for x in case["assumptions"]}
    nodes=assumptions|{"H1","H2"}|{r["consequent"] for r in case["rules"]}
    assert len(assumptions)==len(case["assumptions"])
    assert len({r["id"] for r in case["rules"]})==len(case["rules"])
    assert all(set(r["antecedents"])<=nodes and r["consequent"] not in assumptions for r in case["rules"])
    assert all(set(ng)<=assumptions and len(ng)>1 for ng in case["nogoods"])
    assert case["target_revision"]==case["revisions"][-1]["id"]
    assert all(set(rev["revoked"])<=assumptions for rev in case["revisions"])
    return assumptions

def exhaustive(case):
    a=_case_nodes(case)
    revoked=set(case["revisions"][-1]["revoked"])
    available=sorted(a-revoked)
    supported=set()
    # Explicitly enumerate compatible environments, not truth assignments.
    for n in range(len(available)+1):
        for combination in itertools.combinations(available,n):
            env=frozenset(combination)
            if any(set(ng)<=env for ng in case["nogoods"]):
                continue
            nodes=set(env)
            for _ in range(len(case["rules"])+1):
                new={r["consequent"] for r in case["rules"] if set(r["antecedents"])<=nodes}
                if new<=nodes:
                    break
                nodes |= new
            supported.update(nodes&{"H1","H2"})
    return encode(supported)

def minimal_environments(case):
    a=_case_nodes(case)
    revoked=set(case["revisions"][-1]["revoked"])
    labels={x: {frozenset([x])} if x not in revoked else set() for x in a}
    def compatible(env):
        return not any(set(ng)<=env for ng in case["nogoods"])
    for _ in range((len(a)+1)*(len(case["rules"])+1)):
        changed=False
        for rule in case["rules"]:
            parts=[labels.get(x,set()) for x in rule["antecedents"]]
            if not parts or any(not x for x in parts):
                continue
            proposed={frozenset().union(*p) for p in itertools.product(*parts)}
            proposed={p for p in proposed if compatible(p)}
            old=labels.get(rule["consequent"],set())
            expanded=old|proposed
            reduced={e for e in expanded if not any(t<e for t in expanded)}
            if reduced != old:
                labels[rule["consequent"]]=reduced
                changed=True
        if not changed:
            break
    else:
        raise AssertionError("Logic provenance did not converge")
    return {h:sorted([sorted(e) for e in labels.get(h,set())],key=lambda a:(len(a),a)) for h in ("H1","H2")}

def encode(supported):
    return "BOTH" if {"H1","H2"}<=supported else "ONLY_H1" if "H1" in supported else "ONLY_H2" if "H2" in supported else "NEITHER"

def verified_status(case):
    gold1=exhaustive(case)
    environments=minimal_environments(case)
    gold2=encode({h for h,v in environments.items() if v})
    if gold1!=gold2:
        raise AssertionError("ORACLE_MISMATCH "+case["id"])
    return gold1,environments

def D(value):
    return Decimal(str(value))

def calculate_numeric(case):
    """Pure Decimal state evolution. Clairic output never enters this computation."""
    name=case["family"]
    if name=="balance":
        x=D(case["initial"])
        if len(case["inflows"])!=len(case["outflows"]):
            raise ValueError("Balance arrays differ")
        for income,outcome in zip(case["inflows"],case["outflows"]):
            x+=D(income)-D(outcome)
            if x<0:raise ValueError("Negative stock")
        return x
    if name=="capacity":
        x=D(case["initial"])
        for arrival,request,cap in zip(case["arrivals"],case["requested_service"],case["capacity"],strict=True):
            available=x+D(arrival)
            served=min(available,D(request),D(cap))
            x=available-served
            if x<0:raise AssertionError("Negative backlog")
        return x
    if name=="serial":
        a,b=D(case["a0"]),D(case["b0"])
        for arrival,transfer,departure in zip(case["arrivals_a"],case["transfers_a_to_b"],case["departures_b"],strict=True):
            old_total=a+b
            arr,trans,depart=D(arrival),D(transfer),D(departure)
            if trans>a+arr or depart>b+trans:
                raise ValueError("Unphysical flow")
            a+=arr-trans
            b+=trans-depart
            if a+b!=old_total+arr-depart:
                raise AssertionError("Conservation invariant violated")
        return a if case["target"]=="A_final" else b
    raise ValueError("Unknown mathematical family")

def validate_all():
    cases=json.loads((ROOT/"fixtures/heterogeneous_cases.json").read_text(encoding="utf-8"))["cases"]
    numerics=json.loads((ROOT/"fixtures/math_cases.json").read_text(encoding="utf-8"))["cases"]
    gold=json.loads((ROOT/"evaluation/gold.json").read_text(encoding="utf-8"))
    assert len(cases)==20 and len(numerics)==8
    assert gold["locked_before_provider"] is True
    from collections import Counter
    assert Counter(c["motif"] for c in cases)==dict.fromkeys(("branching","chain","shared","nogoods","restoration"),4)
    recorded={}
    for case in cases:
        state,env=verified_status(case)
        assert state==gold["statuses"][case["id"]],case["id"]
        recorded[case["id"]]={"state":state,"environments":env}
    assert Counter(gold["statuses"].values())==dict.fromkeys(STATES,5)
    for n in numerics:
        value=calculate_numeric(n)
        assert value==D(gold["numerics"][n["id"]]),n["id"]
    return recorded
if __name__=="__main__":
    print(json.dumps({"verified_cases":len(validate_all()),"verified_numerics":8,"inference_calls":0}))

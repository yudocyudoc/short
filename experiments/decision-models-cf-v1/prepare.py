#!/usr/bin/env python3
"""EPI-03: prepare frozen decision/extraction requests. No network, no credentials."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OPTIONS=("BOTH","ONLY_H1","ONLY_H2","NEITHER")
MODELS={"CLEF":"@cf/cloudflare/clef","GLM":"@cf/zai-org/glm-4.7-flash","CLAIRIC":"@cf/cloudflare/clairic"}
MAX_CALLS=36
GOLD=HERE/"evaluation"/"gold.json"
DECISIONS=HERE/"fixtures"/"decision_cases.json"
NUMERICS=HERE/"fixtures"/"numeric_cases.json"
CRITERIA={
"BOTH":"Ambas hipótesis H1 y H2 mantienen al menos una ruta de soporte lógico",
"ONLY_H1":"Solo H1 conserva soporte; H2 no conserva ninguna ruta",
"ONLY_H2":"Solo H2 conserva soporte; H1 no conserva ninguna ruta",
"NEITHER":"Ni H1 ni H2 conserva una ruta de soporte"}
QUESTION="Tras aplicar TODAS las invalidaciones indicadas, ¿qué combinación de soporte lógico se deriva de las reglas AND/OR? Soporte no significa verdad empírica. Elige una opción."

def dump(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sha(b): return hashlib.sha256(b).hexdigest()

def closure(case):
    active={a["id"] for a in case["assumptions"]}-set(case["revoked"])
    known=set(active)
    for _ in range(len(case["rules"])+2):
        new={r["consequent"] for r in case["rules"] if set(r["antecedents"])<=known}
        updated=known|new
        if updated==known: break
        known=updated
    else:
        raise ValueError("Fixed-point did not converge")
    h1,h2=(x in known for x in case["hypotheses"])
    return "BOTH" if h1 and h2 else "ONLY_H1" if h1 else "ONLY_H2" if h2 else "NEITHER"

def case_state(case):
    # Gold, arm identity and evaluator annotations are deliberately absent.
    return dump({k:case[k] for k in ("question","hypotheses","records","assumptions","rules","revoked","steps","scope")})

def ordered_options(case_id):
    n=int(sha(case_id.encode())[:4],16)%4
    return list(OPTIONS[n:]+OPTIONS[:n])

def clef_request(state,case_id):
    return {"model":"clef","state":state,"questions":{"support_state":{
        "type":"choice","instructions":QUESTION,
        "criteria":{x:CRITERIA[x] for x in ordered_options(case_id)}}}}

def glm_request(state,case_id):
    criteria={x:CRITERIA[x] for x in ordered_options(case_id)}
    instructions=("Eres un clasificador de soporte lógico, no un narrador. " + QUESTION +
        " Devuelve SOLO un objeto JSON con las claves choice y probabilities. "+
        "choice debe ser una clave de OPTIONS. probabilities debe dar una probabilidad numérica "+
        "entre 0 y 1 para cada una de las cuatro opciones, sumando 1. "+
        "No confundas soporte formal con probabilidad de verdad empírica. "+
        "No añadas explicaciones ni Markdown.\nOPTIONS="+dump(criteria)+"\nSTATE="+state)
    return {"messages":[{"role":"user","content":instructions}],
            "temperature":0.1,"max_completion_tokens":350,
            "chat_template_kwargs":{"enable_thinking":False}}

def clairic_request(n):
    if n["kind"]=="CALC":
        field={"type":"number","decimals":0,
            "instructions":"Calcula el stock final exacto aplicando las entradas y salidas indicadas."}
    elif n["kind"]=="FORECAST":
        field={"type":"estimate","min":0,"max":100,"step":1,
            "instructions":"Estima el stock del periodo siguiente a partir de los datos históricos. Proporciona mediana e intervalo p10/p90 si es posible."}
    else: raise ValueError("Unknown numeric task")
    return {"model":"clairic","state":n["state"],"fields":{"stock_value":field}}

def make_requests():
    dataset=json.loads(DECISIONS.read_text(encoding="utf-8"))
    nums=json.loads(NUMERICS.read_text(encoding="utf-8"))
    gold=json.loads(GOLD.read_text(encoding="utf-8"))
    cases=dataset["cases"]
    assert len(cases)==14 and sum(c["kind"]=="balanced" for c in cases)==12
    assert len([c for c in cases if c["kind"]=="epi02_anchor"])==2
    assert len(nums["cases"])==8
    assert tuple(dataset["options"])==OPTIONS
    assert gold["locked_before_provider"] is True
    from collections import Counter
    distribution=Counter(gold["classification"][c["id"]] for c in cases if c["kind"]=="balanced")
    assert distribution=={x:3 for x in OPTIONS},distribution
    requests=[]
    for c in cases:
        assert closure(c)==gold["classification"][c["id"]],c["id"]
        source=case_state(c)
        for model in ("CLEF","GLM"):
            body=clef_request(source,c["id"]) if model=="CLEF" else glm_request(source,c["id"])
            requests.append({"id":c["id"],"type":"CLASSIFICATION","stratum":c["kind"],
                             "model":model,"endpoint":MODELS[model],"body":body})
    for n in nums["cases"]:
        assert n["kind"] in ("CALC","FORECAST")
        assert isinstance(gold["numerics"][n["id"]],(float,int))
        requests.append({"id":n["id"],"type":"NUMERIC","stratum":n["kind"],"model":"CLAIRIC",
                         "endpoint":MODELS["CLAIRIC"],"body":clairic_request(n)})
    assert len(requests)==MAX_CALLS
    # Seeded, balanced interleaving rather than grouping arms by model.
    import random
    random.Random(20261021).shuffle(requests)
    for i,r in enumerate(requests,1):
        r["sequence"]=i
        r["body_sha256"]=sha(dump(r["body"]).encode())
    return requests

def prepare(out):
    out.mkdir(parents=True,exist_ok=True)
    req=make_requests()
    payload="".join(dump(x)+"\n" for x in req)
    (out/"requests.jsonl").write_text(payload,encoding="utf-8")
    report={"status":"PREPARED_NO_INFERENCE","calls_planned":MAX_CALLS,"calls_made":0,
            "models":MODELS,"balanced_cases":12,"epi02_anchors":2,"numeric_cases":8,
            "task_counts":{"CLEF":14,"GLM":14,"CLAIRIC":8},
            "gold_sha256":sha(GOLD.read_bytes()),"decision_cases_sha256":sha(DECISIONS.read_bytes()),
            "numeric_cases_sha256":sha(NUMERICS.read_bytes()),
            "requests_sha256":sha(payload.encode())}
    (out/"preparation-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().out),ensure_ascii=False))

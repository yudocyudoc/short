#!/usr/bin/env python3
"""EPI-06 preregistered 2x2 task×instruction design: no inference in preparation."""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from oracle import ROOT,FIXTURES,GOLD,STATES,validate

MODEL="@cf/cloudflare/clef"
MAX_CALLS=80
AUTH="RUN_EPI06_MAX80"
CONDITIONS=("CHOICE_BASE","CHOICE_EXPLICIT","BINARY_BASE","BINARY_EXPLICIT")
CONTEXT=("Usa reglas AND/OR, invalidaciones del ÚLTIMO corte y nogoods de incompatibilidad. "
"Si se restaura un supuesto, vuelve a estar disponible. Comprueba soporte individual, no verdad empírica ni coexistencia.")
STRONG=("Para cada hipótesis exige al menos UNA ruta COMPLETA: TODOS los antecedentes y supuestos de esa ruta "
"deben seguir vigentes en la revisión final y ser compatibles entre sí. Una ruta rota o un fragmento "
"de justificación NO cuenta como soporte. Si ninguna ruta completa sobrevive, esa hipótesis NO tiene soporte.")
CRITERIA={
 "BOTH":"Cada hipótesis tiene al menos un entorno de soporte individualmente consistente. No es necesario que los entornos de ambas hipótesis coexistan.",
 "NEITHER":"Ninguna hipótesis tiene un entorno de soporte consistente.",
 "ONLY_H1":"H1 tiene algún entorno de soporte consistente; H2 no tiene ninguno.",
 "ONLY_H2":"H2 tiene algún entorno de soporte consistente; H1 no tiene ninguno."
}
STATE_KEYS=("scenario","hypotheses","source_records","assumptions","rules","nogoods","revisions","target_revision","task")
def encoded(x):return json.dumps(x,ensure_ascii=False,separators=(",",":"))
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sha(data):return hashlib.sha256(data).hexdigest()

def build(case,condition):
    if condition not in CONDITIONS:raise ValueError("Unexpected experimental condition")
    state=canonical({k:case[k] for k in STATE_KEYS})
    prefix=CONTEXT+(" "+STRONG if condition.endswith("EXPLICIT") else "")
    if condition.startswith("CHOICE"):
        questions={"status":{"type":"choice","instructions":prefix+" ¿Cuál de los cuatro estados de soporte corresponde a H1 y H2?",
          "criteria":CRITERIA.copy()}}
    else:
        questions={
           "h1_supported":{"type":"noul","instructions":prefix+" ¿Existe al menos un entorno de soporte consistente para H1?"},
           "h2_supported":{"type":"noul","instructions":prefix+" ¿Existe al menos un entorno de soporte consistente para H2?"}
        }
    return {"model":"clef","state":state,"questions":questions}

def prepare(out):
    cases,gold=validate()
    reqs=[{"id":c["id"],"condition":condition,"endpoint":MODEL,"body":build(c,condition)}
       for c in cases for condition in CONDITIONS]
    assert len(reqs)==MAX_CALLS
    random.Random(20261021).shuffle(reqs)
    for i,r in enumerate(reqs,1):
        r["sequence"]=i
        r["body_sha256"]=sha(encoded(r["body"]).encode("utf-8"))
    out.mkdir(parents=True,exist_ok=True)
    schedule="".join(encoded(r)+"\n" for r in reqs)
    (out/"requests.jsonl").write_text(schedule,encoding="utf-8")
    report={
       "schema":"short-epi06-preparation/1","status":"PREPARED_NO_INFERENCE",
       "inference_calls":0,"calls_planned":MAX_CALLS,"case_count":len(cases),
       "counts":{"NEITHER":8,"BOTH":4,"ONLY_H1":4,"ONLY_H2":4},
       "conditions":CONDITIONS,"model":MODEL,
       "fixture_sha256":sha(FIXTURES.read_bytes()),"gold_sha256":sha(GOLD.read_bytes()),
       "requests_sha256":sha(schedule.encode("utf-8")),
       "instruction_change_is_common_across_question_modes":True,
       "state_serialization":"JSON string, unchanged for all conditions"
    }
    (out/"preparation-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().out),ensure_ascii=False))

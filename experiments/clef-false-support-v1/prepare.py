#!/usr/bin/env python3
"""EPI-05 controlled 6-condition Clef input ablation. No live calls."""
from __future__ import annotations
import argparse, hashlib, json, random
from pathlib import Path
from oracle import ROOT, FIXTURES, GOLD, STATES, validate

MODEL="@cf/cloudflare/clef"
AUTH="RUN_EPI05_MAX48"
CONDITIONS=(
    "BASE_STRING_CHOICE",
    "OBJECT_CHOICE",
    "BASE_STRING_BINARY",
    "OBJECT_BINARY",
    "EXPLICIT_ACTIVE_CHOICE",
    "REVERSED_OPTIONS_CHOICE",
)
QUESTION=("Usa reglas AND/OR, invalidaciones del ÚLTIMO corte y nogoods de incompatibilidad. "
"Si se restaura un supuesto, vuelve a estar disponible. Comprueba soporte individual, "
"no verdad empírica ni coexistencia. ¿Qué hipótesis conserva al menos un entorno de soporte consistente?")
CRITERIA={
    "BOTH":"Cada hipótesis tiene al menos UN entorno de soporte individualmente consistente. No tienen que coexistir ambas en el mismo entorno.",
    "NEITHER":"Ninguna hipótesis tiene un entorno de soporte consistente.",
    "ONLY_H1":"H1 tiene algún entorno de soporte consistente; H2 no tiene ninguno.",
    "ONLY_H2":"H2 tiene algún entorno de soporte consistente; H1 no tiene ninguno.",
}
STATE_KEYS=("scenario","hypotheses","source_records","assumptions","rules","nogoods","revisions","target_revision","task")
MAX_CALLS=48

def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def transport(x):return json.dumps(x,ensure_ascii=False,separators=(",",":"))
def sha(x):return hashlib.sha256(x).hexdigest()

def public_state(case):
    return {k:case[k] for k in STATE_KEYS}

def derived_active(case):
    assume={a["id"] for a in case["assumptions"]}
    revoked=set(case["revisions"][-1]["revoked"])
    return sorted(assume-revoked)

def question_choice(reverse=False):
    criteria=dict(reversed(list(CRITERIA.items()))) if reverse else dict(CRITERIA)
    return {"status":{"type":"choice","instructions":QUESTION,"criteria":criteria}}

def question_binary():
    return {
     "h1_supported":{"type":"noul","instructions":("¿Tiene H1 AL MENOS UNA ruta de soporte completa con TODOS sus supuestos vigentes y sin nogoods, tras la última revisión? Una ruta parcialmente satisfecha NO cuenta.")},
     "h2_supported":{"type":"noul","instructions":("¿Tiene H2 AL MENOS UNA ruta de soporte completa con TODOS sus supuestos vigentes y sin nogoods, tras la última revisión? Una ruta parcialmente satisfecha NO cuenta.")}
    }

def build(case,condition):
    state=public_state(case)
    if condition=="EXPLICIT_ACTIVE_CHOICE":
        # Add only deterministic status of primitive assumptions; never include derived H1/H2 status.
        state["active_assumptions"]=derived_active(case)
        state["revoked_assumptions"]=sorted(case["revisions"][-1]["revoked"])
    as_obj=condition in ("OBJECT_CHOICE","OBJECT_BINARY")
    payload=state if as_obj else canonical(state)
    questions=question_binary() if condition.endswith("BINARY") else question_choice(condition=="REVERSED_OPTIONS_CHOICE")
    return {"model":"clef","state":payload,"questions":questions}

def build_schedule():
    cases,gold=validate()
    requests=[{
       "id":case["id"],"source_motif":case["motif"],"condition":condition,
       "model":"CLEF","endpoint":MODEL,"body":build(case,condition)}
       for case in cases for condition in CONDITIONS]
    assert len(requests)==MAX_CALLS
    random.Random(20261021).shuffle(requests)
    for i,r in enumerate(requests,1):
        r["sequence"]=i
        # The TRANSPORT digest preserves criteria insertion order.
        r["body_sha256"]=sha(transport(r["body"]).encode("utf-8"))
    return requests

def prepare(out):
    requests=build_schedule()
    out.mkdir(parents=True,exist_ok=True)
    data="".join(transport(x)+"\n" for x in requests)
    (out/"requests.jsonl").write_text(data,encoding="utf-8")
    result={
       "schema":"short-epi05-preparation/1","status":"PREPARED_NO_INFERENCE",
       "cases":8,"conditions":list(CONDITIONS),"calls_planned":48,"calls_made":0,
       "model":MODEL,"purpose":"diagnose false support (NEITHER) with state modality, binary decomposition, active primitive status and option order",
       "source_commit":"047911d739676b15721fdafde20faad49387c250",
       "fixture_sha256":sha(FIXTURES.read_bytes()),"gold_sha256":sha(GOLD.read_bytes()),
       "requests_sha256":sha(data.encode("utf-8"))
    }
    (out/"preparation-report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    print(json.dumps(prepare(parser.parse_args().out),ensure_ascii=False))

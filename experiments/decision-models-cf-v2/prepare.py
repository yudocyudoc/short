#!/usr/bin/env python3
"""EPI-04 frozen paired requests. Zero inference, no network or credentials."""
from __future__ import annotations
import argparse,hashlib,json,random
from pathlib import Path
from oracle import ROOT,STATES,validate_all

MODELS={"CLEF":"@cf/cloudflare/clef","GLM":"@cf/zai-org/glm-4.7-flash","CLAIRIC":"@cf/cloudflare/clairic"}
MAX_CALLS=48
DECISIONS=ROOT/"fixtures/heterogeneous_cases.json"
NUMERICS=ROOT/"fixtures/math_cases.json"
GOLD=ROOT/"evaluation/gold.json"
CRITERIA={
"BOTH":"Cada hipótesis tiene al menos UN entorno de soporte individualmente consistente. No tienen que coexistir ambas en el mismo entorno.",
"ONLY_H1":"H1 tiene algún entorno de soporte consistente; H2 no tiene ninguno.",
"ONLY_H2":"H2 tiene algún entorno de soporte consistente; H1 no tiene ninguno.",
"NEITHER":"Ninguna hipótesis tiene un entorno de soporte consistente."
}
QUESTION=("Usa reglas AND/OR, invalidaciones del ÚLTIMO corte y nogoods de incompatibilidad. "
"Si se restaura un supuesto, vuelve a estar disponible. Comprueba soporte individual, no verdad empírica ni coexistencia. "
"¿Qué hipótesis conserva al menos un entorno de soporte consistente?")
def dump(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sha(b):return hashlib.sha256(b).hexdigest()

def options(case_id):
    offset=int(sha(case_id.encode())[-2:],16)%4
    return STATES[offset:]+STATES[:offset]

def state(case):
    public={k:case[k] for k in ("scenario","hypotheses","source_records","assumptions","rules","nogoods","revisions","target_revision","task")}
    # Do not expose motif, expected label, mathematical oracle or gold.
    return dump(public)

def clef_body(public_state,cid):
    return {"model":"clef","state":public_state,
            "questions":{"status":{"type":"choice","instructions":QUESTION,
            "criteria":{x:CRITERIA[x] for x in options(cid)}}}}

def glm_body(public_state,cid):
    instruction=("Eres un clasificador de soporte deductivo. No redactes explicaciones. "
        +QUESTION+" Salida: un solo objeto JSON con choice y probabilities. "
        "choice es una clave del catálogo. probabilities contiene una probabilidad numérica entre 0 y 1 "
        "por cada clave y todas suman uno. Evita Markdown. "
        "Las probabilidades son confianza de CLASIFICACIÓN, no posterior de verdad empírica."
        "\nOPTIONS="+dump({x:CRITERIA[x] for x in options(cid)})
        +"\nSTATE="+public_state)
    return {"messages":[{"role":"user","content":instruction}],
            "temperature":0.1,"max_completion_tokens":360,
            "chat_template_kwargs":{"enable_thinking":False}}

def numeric_state(n):
    public={k:v for k,v in n.items() if k!="id"}
    public["conventions"]="Periodos sucesivos; los flujos internos A→B no crean material. No adivinar datos faltantes."
    return dump(public)

def clairic_body(n):
    return {"model":"clairic","state":numeric_state(n),
            "fields":{"calculated_value":{"type":"number","decimals":2,
            "instructions":("Aplica exactamente el sistema discreto por periodos descrito en el estado. "
             "Para balance, stock final = inicial + entradas - salidas. "
             "Para capacity, servicio=min(stock disponible, solicitud, capacidad). "
             "Para serial, actualiza ambos compartimentos y conserva masa al transferir internamente. "
             "Devuelve únicamente el valor de target, sin estimación probabilística ni sustitución del oráculo determinista.")}}}

def assemble():
    validate_all()
    decisions=json.loads(DECISIONS.read_text(encoding="utf-8"))["cases"]
    numeric=json.loads(NUMERICS.read_text(encoding="utf-8"))["cases"]
    requests=[]
    for c in decisions:
        s=state(c)
        for model in ("CLEF","GLM"):
            b=clef_body(s,c["id"]) if model=="CLEF" else glm_body(s,c["id"])
            requests.append({"id":c["id"],"motif":c["motif"],"kind":"classification",
               "model":model,"endpoint":MODELS[model],"body":b})
    for n in numeric:
        requests.append({"id":n["id"],"motif":n["family"],"kind":"arithmetic",
                         "model":"CLAIRIC","endpoint":MODELS["CLAIRIC"],"body":clairic_body(n)})
    assert len(requests)==MAX_CALLS
    random.Random(20261021).shuffle(requests)
    for seq,r in enumerate(requests,1):
        r["sequence"]=seq
        r["body_sha256"]=sha(dump(r["body"]).encode())
    return requests

def prepare(out):
    requests=assemble()
    out.mkdir(parents=True,exist_ok=True)
    content="".join(dump(req)+"\n" for req in requests)
    (out/"requests.jsonl").write_text(content,encoding="utf-8")
    manifest={"schema":"short-epi04-preparation/1","status":"PREPARED_NO_INFERENCE",
       "calls_planned":MAX_CALLS,"calls_made":0,"models":MODELS,
       "classification_cases":20,"math_crosschecks":8,
       "counts_by_model":{"CLEF":20,"GLM":20,"CLAIRIC":8},
       "design":"five graph families, four states per family, no repeated calls; 8 independent Decimal validations",
       "gold_sha256":sha(GOLD.read_bytes()),"decisions_sha256":sha(DECISIONS.read_bytes()),
       "math_sha256":sha(NUMERICS.read_bytes()),"requests_sha256":sha(content.encode())}
    (out/"preparation-report.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    print(json.dumps(prepare(p.parse_args().out),ensure_ascii=False))

#!/usr/bin/env python3
"""IA-1: one-shot evidence extraction + real molecular AST proposal.

12 authored Spanish vignettes, not secret real-world worlds. Llama via Cloudflare
Workers AI. Same input for a preregistered lexical/no-LLM baseline.

No rubric, gold, topology key, or expected response is put in model messages.
Scores are descriptive, author-coded, and NOT causal-world identification.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/"experiments"/"e1"))
import composer
import backend

MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
MAX_OUT=2600
CATEGORIES=("SUPPORTED","UNRESOLVED")
ALLOWED={"case_id","physical_post_dispatch","informational_transform",
         "architecture","unresolved","topology_claim"}
ROLE_KEY={
 "physical_post_dispatch":"transit",
 "informational_transform":"report",
}
SYSTEM="""Eres arquitecto de hipótesis en dinámica de sistemas, no adivinador de la verdad.
Distingue observaciones directamente documentadas, mecanismos hipotéticos y lo que NO puede inferirse.
La descripción nunca identifica de forma única la topología o los parámetros.
SUPPORTED significa que hay HECHOS DIRECTOS que respaldan considerar esa familia de mecanismo,
NO que se haya probado matemáticamente una ecuación de primer orden.
UNRESOLVED significa que no hay evidencia suficiente, aunque sea posible.
- physical_post_dispatch: evidencia positiva de UNIDADES FÍSICAS acumuladas DESPUÉS del despacho y ANTES de recepción real.
  Una cola anterior al despacho NO cuenta. Retraso sólo del tablero tampoco.
- informational_transform: evidencia positiva de una TRANSFORMACIÓN DE LA SEÑAL del tablero relativa a recepción física;
  retraso entre despacho y tablero, sin medición de recepción física, NO basta.
- Si hechos se contradicen sin resolución, abstente; nunca resuelvas por preferencia.
Usa citas SOLO por IDs existentes; para UNRESOLVED puedes citar hechos que muestran falta de observabilidad.
Propón UN ÚNICO AST ejecutable como HIPÓTESIS ilustrativa, no como topología identificada.
El AST usa moléculas verificadas, nunca escribe ecuaciones, y puede ser simple ante insuficiencia.
No recibes gráficos verdaderos, gold, tablas de firma ni respuestas de oráculo.
Devuelve un único JSON (sin comentario externo ni Markdown):
{
 "case_id":"...",
 "physical_post_dispatch":{"status":"SUPPORTED|UNRESOLVED","fact_ids":["F1"]},
 "informational_transform":{"status":"SUPPORTED|UNRESOLVED","fact_ids":[]},
 "architecture":{"instances":[{"id":"...", "class_id":"...", "role":"...", "parameters":{}}],
                 "links":[{"from":"instance.port","to":"instance.port","adapter":null}]},
 "unresolved":["pregunta o limitación en español"],
 "topology_claim":"HYPOTHESIS_NOT_IDENTIFIED"
}
EXACTAMENTE esas claves; no cambies esquema, no inventes IDs ni papeles o clases.
Tipos de flujo / adaptadores y parámetros están en registro público. No incluyas el estímulo en el AST.
Toda salida es una propuesta exploratoria sujeta a compilación; no puedes concluir unicidad.
"""


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path,obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


def archive_text(path,content):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(content,encoding="utf-8")


def case_items():
    return read(HERE/"cases.json")["cases"]


def source_contract():
    cfg,classes,_=composer.load_registry(ROOT/"experiments/e1/registry.base.json")
    # Freeze only factual capability of catalog, no graph enumeration, no solved AST.
    elements=[]
    for role, spec in cfg["roles"].items():
        cl=classes[spec["class_id"]]
        elements.append({
            "role":role,"class_id":spec["class_id"],"modelica":cl["modelica"],
            "max_instances":spec["max_instances"],
            "fixed_parameters":spec["parameters"],
            "ports":composer.ports(cl,role)
        })
    return {
        "registered_roles":elements,
        "material_typed_links":"identical FLOW<X> out -> FLOW<X> in",
        "required_roles":cfg["mandatory_roles"],
        "information_tap":{
           "adapter":"receipt-rate-tap",
           "rule":"From the very flow entering the physical receipt to the input of the report filter; FLOW<Shipment> to SIGNAL<DeliveryRate>; does not move material."
        },
        "output_format":"Existing E1 AST: instances and links. No new differential equations.",
        "uncertainty":"Stage count and parameters are NOT identified from these narratives."
    }


def messages(case):
    public_case={"id":case["id"],"context":case["context"],"facts":case["facts"]}
    return [{"role":"system","content":SYSTEM},
            {"role":"user","content":json.dumps({
               "case":public_case,
               "registry_contract":source_contract(),
               "task":"Identifica evidencia respaldada y dudas, después propone UN AST ilustrativo. No afirmes arquitectura verdadera."
              },ensure_ascii=False)}]


def parse_text(raw):
    t=raw.strip()
    fence=chr(96)*3
    if t.startswith(fence):
        match=re.fullmatch(re.escape(fence)+r"(?:json)?\s*([\s\S]*?)\s*"+re.escape(fence),t)
        if not match:
            raise ValueError("NON_SINGLE_FENCE")
        t=match.group(1).strip()
    obj=json.loads(t)
    if not isinstance(obj,dict):
        raise ValueError("TOP_LEVEL_NOT_JSON_OBJECT")
    return obj


def validate(case,proposal):
    failures=[]
    if not isinstance(proposal,dict) or set(proposal)!=ALLOWED:
        return {"status":"INVALID","issues":["OUTPUT_SCHEMA"],"ast_valid":False}
    if proposal["case_id"]!=case["id"]:
        failures.append("CASE_ID")
    facts={f["id"] for f in case["facts"]}
    for dim in ROLE_KEY:
        d=proposal[dim]
        if not isinstance(d,dict) or set(d)!={"status","fact_ids"}:
            failures.append("EVIDENCE_DIMENSION_SCHEMA:"+dim)
            continue
        if d["status"] not in CATEGORIES:
            failures.append("INVALID_STATUS:"+dim)
        refs=d["fact_ids"]
        if not isinstance(refs,list) or not all(isinstance(ref,str) and ref in facts for ref in refs) or len(refs)!=len(set(refs)):
            failures.append("BAD_FACT_IDS:"+dim)
        elif d["status"]=="SUPPORTED" and not refs:
            failures.append("SUPPORTED_WITHOUT_FACTS:"+dim)
    if proposal["topology_claim"]!="HYPOTHESIS_NOT_IDENTIFIED":
        failures.append("UNJUSTIFIED_TOPOLOGY_CLAIM")
    if not isinstance(proposal["unresolved"],list) or not all(isinstance(x,str) and len(x)<280 for x in proposal["unresolved"]):
        failures.append("INVALID_UNRESOLVED")
    elif not proposal["unresolved"]:
        failures.append("NO_UNCERTAINTY")
    ast=proposal["architecture"]
    ast_valid=False
    if not isinstance(ast,dict):
        failures.append("NO_AST")
    else:
        try:
            cfg,cl,_=composer.load_registry(ROOT/"experiments/e1/registry.base.json")
            composer.check_graph(ast,cfg,cl)
            backend.render_model("CaseCandidate",ast,cfg,cl)
            valid_keys={"instances","links"}
            if set(ast)!=valid_keys:
                raise ValueError("EXTRA_AST_KEYS")
            for ins in ast["instances"]:
                registered=cfg["roles"].get(ins.get("role"))
                if not registered or set(ins)!={"id","role","class_id","parameters"}:
                    raise ValueError("AST_INSTANCE_SCHEMA")
                if ins["class_id"]!=registered["class_id"] or ins["parameters"]!=registered["parameters"]:
                    raise ValueError("NONREGISTERED_PARAMS")
            ast_valid=True
        except (ValueError,TypeError,KeyError,IndexError,StopIteration,AssertionError) as exc:
            failures.append("AST_INVALID:"+str(exc)[:90])
    return {"status":"VALID" if not failures else "INVALID",
            "issues":failures,"ast_valid":ast_valid,
            "semantic_judgments_verified":False}


def baseline(case):
    """Simple baseline, fixed before model run. Matches signals, NOT gold labels."""
    string=" ".join(f["text"] for f in case["facts"]).lower()
    # A deliberately simple lexical baseline, not an exhaustive topological solver.
    physical=any(s in string for s in (
        "todavía no habían llegado", "unidades previamente expedidas",
        "se acumularon unidades expedidas","pendientes de recibir",
        "ubicado físicamente dentro de vehículos",
        "unidades se reciben físicamente en el siguiente turno"
    ))
    info=any(s in string for s in (
        "promedio móvil","media temporal","suaviza","ajuste temporal",
        "promedio ponderado"
    ))
    decision={
        "physical_post_dispatch":{"status":"SUPPORTED" if physical else "UNRESOLVED","fact_ids":[]},
        "informational_transform":{"status":"SUPPORTED" if info else "UNRESOLVED","fact_ids":[]}
    }
    # For supported decisions cite every fact (permissive: semantic validity still separately scored).
    for dim in decision:
        if decision[dim]["status"]=="SUPPORTED":
            decision[dim]["fact_ids"]=[x["id"] for x in case["facts"]]
    cfg,cl,_=composer.load_registry(ROOT/"experiments/e1/registry.base.json")
    options=composer.enumerate_graphs(cfg,cl)
    # Candidate deliberately fixed and evidence-agnostic; valid AST is not discovery.
    minimal=next(g for _,g in options if len(g["instances"])==4)
    return {"case_id":case["id"],**decision,"architecture":copy.deepcopy(minimal),
            "unresolved":["No puede identificarse una topología única con estos hechos."],
            "topology_claim":"HYPOTHESIS_NOT_IDENTIFIED"}


def cloudflare_call(account,token,ms):
    payload={"messages":ms,"temperature":0,"stream":False,"max_tokens":MAX_OUT}
    request=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+MODEL,
       data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),method="POST",
       headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
    with urlopen(request,timeout=150) as f:
        data=json.load(f)
    if not isinstance(data,dict) or data.get("success") is False:
        raise ValueError("PROVIDER_UNSUCCESSFUL")
    body=data.get("result",data)
    raw=body.get("response") if isinstance(body,dict) else None
    if not isinstance(raw,str) and isinstance(body,dict):
        choices=body.get("choices")
        if isinstance(choices,list) and choices:
            raw=choices[0].get("message",{}).get("content")
    if not isinstance(raw,str):
        raise ValueError("NO_MODEL_TEXT")
    return data,raw


def score_run(out,executed):
    judgments={x["id"]:x for x in read(HERE/"evaluation_gold.json")["judgments"]}
    cases=case_items()
    results={}
    for arm in ("lexical","llama"):
        rows=[]
        for case in cases:
            id=case["id"]
            filename=Path(out)/arm/id/"result.json"
            if arm=="llama" and not executed and not filename.exists():
                continue
            entry=read(filename)
            proposal=entry.get("proposal")
            lint=entry.get("linter",{})
            is_valid=lint.get("status")=="VALID"
            gold=judgments[id]
            dim_scores={}
            for dim,expected_key in (
                ("physical_post_dispatch","physical_post_dispatch_evidence"),
                ("informational_transform","informational_transform_evidence")
            ):
                response=proposal.get(dim) if is_valid and isinstance(proposal,dict) else None
                matching=(isinstance(response,dict) and response.get("status")==gold[expected_key])
                supported=gold[expected_key]=="SUPPORTED"
                refs=response.get("fact_ids",[]) if isinstance(response,dict) else []
                anchors=gold["primary_anchors"]
                citation=not supported or any(ref in anchors for ref in refs)
                dim_scores[dim]={"correct_status":bool(matching),
                    "anchor_cited":bool(citation) if matching else False,
                    "strict_evidence":bool(matching and citation)}
            rows.append({"id":id,"admitted":is_valid,"ast_valid":lint.get("ast_valid",False),
                "physical":dim_scores["physical_post_dispatch"],
                "information":dim_scores["informational_transform"],
                "both_evidence_strict":all(x["strict_evidence"] for x in dim_scores.values()),
                "error":entry.get("error")})
        results[arm]={
          "n":len(rows),
          "strict_admitted":sum(x["admitted"] for x in rows),
          "valid_ast":sum(x["ast_valid"] for x in rows),
          "strict_both_evidence":sum(x["both_evidence_strict"] for x in rows),
          "strict_physical":sum(x["physical"]["strict_evidence"] for x in rows),
          "strict_information":sum(x["information"]["strict_evidence"] for x in rows),
          "rows":rows}
    return {"status":"DESCRIPTIVE_AUTHOR_CODED","sampling":"N=12 authored; not independent blind benchmark",
            "question":"Evidence extraction and AST validity, not structural truth identification",
            "model":MODEL,"temperature":0,
            "llm_calls_planned":len(cases),"arms":results,
            "no_claims":["No unique topology identifiable","No causal-world oracle used",
                         "No statistical superiority inference", "Zero-temperature repeated calls are not independent observations"]}


def run(out,execute):
    out=Path(out)
    cases=case_items()
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if execute and not (account and token):
        raise SystemExit("NO_CLOUDFLARE_SECRETS")
    for c in cases:
        msgs=messages(c)
        model_folder=out/"llama"/c["id"]
        save(model_folder/"request_without_secrets.json",
            {"model":MODEL,"max_tokens":MAX_OUT,"temperature":0,"messages":msgs})
        baseline_proposal=baseline(c)
        save(out/"lexical"/c["id"]/"result.json",{
            "proposal":baseline_proposal,"linter":validate(c,baseline_proposal),
            "run_type":"DETERMINISTIC_BASELINE_NO_GOLD"
        })
        if execute:
            try:
                provider,raw=cloudflare_call(account,token,msgs)
                save(model_folder/"provider_original.json",provider)
                archive_text(model_folder/"original_llm.txt",raw)
                proposal=parse_text(raw)
                lint=validate(c,proposal)
                result={"proposal":proposal,"linter":lint,
                        "raw_sha256":hashlib.sha256(raw.encode()).hexdigest()}
            except (HTTPError,URLError,TimeoutError,ValueError,TypeError,KeyError) as exc:
                result={"error":{"class":type(exc).__name__},
                        "linter":{"status":"INVALID","issues":["CALL_OR_FORMAT_FAILED"],"ast_valid":False}}
            save(model_folder/"result.json",result)
            print("IA1_LLM_CASE",json.dumps({"id":c["id"],
                "valid":result["linter"]["status"],"ast":result["linter"].get("ast_valid")}),flush=True)
    result=score_run(out,execute)
    save(out/"score.json",result)
    print("IA1_FINAL",json.dumps({
        "n":len(cases),
        "lexical":{k:v for k,v in result["arms"]["lexical"].items() if k!="rows"},
        "llama":{k:v for k,v in result["arms"]["llama"].items() if k!="rows"},
        "status":result["status"]
        },ensure_ascii=False),flush=True)


def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only",action="store_true")
    mode.add_argument("--execute",action="store_true")
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    run(args.out,args.execute)


if __name__=="__main__":
    main()

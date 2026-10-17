#!/usr/bin/env python3
"""One pass: deterministic candidates + OMC signatures -> Llama critic -> machine filtering.

No synthesis of equations or graphs by Llama. The reviewer proposes a
behavioral expectation and supporting fact IDs, not a model verdict.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from explorer import (HERE,TEST_ID,read,enumerate_candidates,
  derive_actual_signatures,validate_review,apply_review,unification_only)

MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
SYSTEM="""Eres un revisor crítico causal; NO eres arquitecto de ecuaciones.
Una máquina ya enumeró y tipó TODOS los candidatos. OpenModelica ya simuló
una prueba registrada sin pedidos nuevos. Tu función NO es elegir el nombre
de un modelo ni aprobar el que te parezca bonito. Debes leer los hechos de
la organización y proponer cuál sería el resultado de la misma prueba EN ESA
ORGANIZACIÓN: STOPS si sin pedidos no fabrica, CONTINUES si sigue fabricando,
UNKNOWN si los hechos no permiten determinarlo, CONFLICT si dos hechos
vigentes se contradicen. No inventes datos, valores, fórmulas ni Modelica.
Los comportamientos de los candidatos son sólo hipótesis de simulación.
No confundas compatibilidad mecánica con soporte empírico. Usa exclusivamente
los IDs de hechos existentes para justificar la expectativa; NO copies las
citas ni intentes crear evidencia por silencio. Si UNKNOWN o CONFLICT,
plantea una pregunta concreta que permitiría distinguir alternativas.
Devuelve solo un JSON:
{"case_id":"R01","test_id":"NO_ACCEPTED_ORDERS",
 "expected":"STOPS|CONTINUES|UNKNOWN|CONFLICT",
 "fact_ids":["F1"],"next_question":""}
No escribas Markdown ni el nombre de la arquitectura elegida."""
def sha(x):return hashlib.sha256(x.encode("utf-8")).hexdigest()
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def messages(case,candidates,signatures):
    # No raw numbers, no answer key, no formulae, no numeric scenario details.
    options=[{"id":c["id"],"meaning":c["meaning"],"exclusions":c["exclusions"],
         "typed_ports_accepted":c["structurally_valid"],
         "simulated_behavior_when_no_orders":signatures[c["id"]]}
         for c in candidates]
    return [
      {"role":"system","content":SYSTEM},
      {"role":"user","content":json.dumps({
         "question":"Propón el comportamiento esperado por los hechos para el ensayo sin nuevos pedidos.",
         "facts":case["facts"],"case_id":case["id"],
         "available_candidates":options,"registered_test":TEST_ID,
         "restriction":"No numerical parameters or equations are available."},ensure_ascii=False)}]
def parse(raw):
    t=raw.strip()
    marker=chr(96)*3
    if t.startswith(marker):
        m=re.fullmatch(re.escape(marker)+r"(?:json)?\s*([\s\S]*?)\s*"+re.escape(marker),t)
        if not m:raise ValueError("BAD_MARKDOWN_FENCE")
        t=m.group(1).strip()
    d=json.loads(t)
    if not isinstance(d,dict):raise ValueError("EXPECTED_OBJECT")
    return d
def cloudflare(account,token,msgs):
    payload={"messages":msgs,"stream":False,"temperature":0,"max_tokens":650}
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+MODEL,
      data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
      headers={"Content-Type":"application/json","Authorization":"Bearer "+token},method="POST")
    with urlopen(req,timeout=120) as f:provider=json.load(f)
    if not isinstance(provider,dict) or provider.get("success") is False:raise ValueError("PROVIDER_ERROR")
    data=provider.get("result",provider)
    txt=data.get("response") if isinstance(data,dict) else None
    if not isinstance(txt,str) and isinstance(data,dict):
        choices=data.get("choices")
        if isinstance(choices,list) and choices:
            txt=choices[0].get("message",{}).get("content")
    if not isinstance(txt,str):raise ValueError("EMPTY_RESPONSE")
    return provider,txt
def evaluate(records):
    gold=read(HERE/"gold.json")["labels"]
    rows=[]
    for case in read(HERE/"cases.json")["cases"]:
        r=records.get(case["id"],{})
        observed=r.get("review",{}).get("expected") if r.get("linter",{}).get("status")=="VALID_REFERENCE_FORMAT" else "INVALID"
        rows.append({"case_id":case["id"],"expected_frozen":gold[case["id"]],
          "reviewer_intent":observed,"matches_expected":observed==gold[case["id"]],
          "retained":r.get("filter",{}).get("kept"),"linter":r.get("linter",{}).get("status")})
    return {"cases":rows,"matched":sum(x["matches_expected"] for x in rows),"n":len(rows),
      "baseline_type_only_keeps_both_for_all_cases":True,
      "limitations":"Four synthetic project-authored cases; model reviewer sees candidate behaviors. Fact-ID validity does not establish semantic truth. Scoring reflects an engineering smoke test, not independent research validation."}
def run(probes,out,execute):
    pool=enumerate_candidates()
    signatures=derive_actual_signatures(probes)
    if len(pool)!=2 or len({p["id"] for p in pool})!=2 or set(signatures)!={p["id"] for p in pool}:
        raise ValueError("INCONSISTENT_ENUMERATOR_OR_OMC_SIGNATURES")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if execute and not(account and token):raise SystemExit("NO_CLOUDFLARE_SECRETS")
    records={}
    for case in read(HERE/"cases.json")["cases"]:
        folder=out/case["id"]
        msgs=messages(case,pool,signatures)
        save(folder/"request_without_secrets.json",{"model":MODEL,"messages":msgs,"temperature":0,"max_tokens":650})
        record={"case_id":case["id"],"enum_candidates":[p["id"] for p in pool],
          "type_only_survivors":unification_only(pool),"request_sha256":sha(json.dumps(msgs,ensure_ascii=False))}
        if execute:
            try:
                provider,raw=cloudflare(account,token,msgs)
                save(folder/"provider_original.json",provider)
                (folder/"llm_original.txt").write_text(raw,encoding="utf-8")
                proposal=parse(raw)
                checks=validate_review(case,proposal)
                record.update({"review":proposal,"linter":checks,"raw_sha256":sha(raw)})
                if checks["status"]=="VALID_REFERENCE_FORMAT":
                    record["filter"]=apply_review(pool,signatures,proposal)
            except (HTTPError,URLError,ValueError,TypeError,KeyError,TimeoutError) as exc:
                record["error"]={"type":type(exc).__name__,"phase":"request_or_parse"}
        records[case["id"]]=record
        save(out/"records.json",records)
        print("IGC_CRITIC_CASE",json.dumps({"case":case["id"],"review_valid":record.get("linter",{}).get("status"),"kept":record.get("filter",{}).get("kept")},ensure_ascii=False),flush=True)
    if execute:
        results=evaluate(records)
        save(out/"evaluation.json",results)
        print("IGC_CRITIC_RESULT",json.dumps({"matched":results["matched"],"n":results["n"]}),flush=True)
    else:print("PREPARED_ONLY_NO_LLAMA_CALLS",flush=True)
def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare-only",action="store_true")
    group.add_argument("--execute",action="store_true")
    p.add_argument("--probes",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    run(a.probes,a.out,a.execute)
if __name__=="__main__":main()

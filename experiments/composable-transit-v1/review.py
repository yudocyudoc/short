#!/usr/bin/env python3
"""LLM as conditional causal critic over independently generated Modelica graphs.

The reviewer cannot propose Modelica code or choose graphs; it proposes a
qualitative interpretation of a pre-executed discriminating counterfactual.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
HERE=Path(__file__).resolve().parent
MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
EXPECTED={"SYNC","LAG","UNKNOWN","CONFLICT"}
TEST="DISPATCH_TO_DELIVERY_LAG"
SYSTEM="""Eres revisor causal adversarial de dinámica de sistemas. El generador
determinista ya creó DOS grafos distintos usando o no una molécula opcional
que retiene unidades en tránsito. El compilador comprobó conexiones y
OpenModelica ejecutó dos ensayos. El primero, sin pedidos, NO distingue
los modelos: ambos detienen su actividad. El segundo detecta si el ritmo
de entrega ocurre al despachar (SYNC) o queda desfasado por un stock real
en tránsito (LAG). Tu función es identificar qué comportamiento esperaríamos
EN EL NEGOCIO descrito, citando únicamente los IDs de hechos observados.
No escribas grafos, fórmulas, cifras ni código. No tienes autorización para
descartar una arquitectura basándote solamente en que sus puertos compilan.
Si faltan datos relevantes indica UNKNOWN; si dos hechos describen políticas
incompatibles del mismo proceso y periodo indica CONFLICT. Para estas dos
opciones formula UNA pregunta de observación discriminante, sin contestarla
con imaginación. Devuelve ÚNICAMENTE objeto JSON con claves exactas:
{"case_id":"C01","test_id":"DISPATCH_TO_DELIVERY_LAG",
"expected":"SYNC|LAG|UNKNOWN|CONFLICT",
"fact_ids":["F1"],"next_question":""}
Para SYNC o LAG fact_ids debe contener hechos relevantes. Para CONFLICT
al menos dos hechos contradictorios. Para UNKNOWN y CONFLICT next_question
no puede ser vacío. No copies ni alteres el texto de los hechos."""
def read(f):return json.loads(Path(f).read_text(encoding="utf-8"))
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def parse(raw):
    s=raw.strip();fence=chr(96)*3
    if s.startswith(fence):
        m=re.fullmatch(re.escape(fence)+r"(?:json)?\s*([\s\S]*?)\s*"+re.escape(fence),s)
        if not m:raise ValueError("BAD_JSON_FENCE")
        s=m.group(1).strip()
    x=json.loads(s)
    if not isinstance(x,dict):raise ValueError("NOT_OBJECT")
    return x
def validate(case,x):
    errors=[]
    if not isinstance(x,dict) or set(x)!={"case_id","test_id","expected","fact_ids","next_question"}:
        return {"status":"INVALID","issues":["SCHEMA"]}
    if x["case_id"]!=case["id"]:errors.append("WRONG_CASE")
    if x["test_id"]!=TEST:errors.append("UNREGISTERED_EXPERIMENT")
    if x["expected"] not in EXPECTED:errors.append("BAD_EXPECTATION")
    ids=x["fact_ids"]
    supported={f["id"] for f in case["facts"]}
    if not isinstance(ids,list) or len(ids)!=len(set(ids)) or not all(isinstance(i,str) and i in supported for i in ids):
        errors.append("EVIDENCE_ID")
    if x["expected"] in {"SYNC","LAG"} and not ids:errors.append("MISSING_SUPPORT")
    if x["expected"]=="CONFLICT" and len(ids)<2:errors.append("MISSING_COUNTERFACT")
    q=x["next_question"]
    if not isinstance(q,str) or len(q)>240 or (x["expected"] in {"UNKNOWN","CONFLICT"} and not q.strip()):
        errors.append("QUESTION_REQUIRED")
    return {"status":"VALID_FORMAT" if not errors else "INVALID",
       "issues":errors,"semantic_entailment_verified":False}

def messages(case,probe):
    aliases={"Direct":"El despacho y la entrega ocurren al mismo ritmo",
             "Buffered":"Existe acumulación y desfase entre despacho y recepción"}
    options=[{"id":name,"simulated_second_test":probe["signatures"][TEST][name],
       "description":aliases[name]} for name in sorted(probe["signatures"][TEST])]
    return [{"role":"system","content":SYSTEM},
     {"role":"user","content":json.dumps({
       "case_id":case["id"],"facts":case["facts"],
       "first_test_id":"NO_ACCEPTED_ORDERS",
       "first_test_signatures":probe["signatures"]["NO_ACCEPTED_ORDERS"],
       "second_test_id":probe["best_discriminating_test"],
       "second_test_signatures":options,
       "question":"¿Cuál comportamiento del segundo ensayo se sostiene por los hechos? Si no se puede saber, no descartes ninguna alternativa."},ensure_ascii=False)}]
def cloudflare(account,token,msgs):
    payload={"messages":msgs,"temperature":0,"max_tokens":700,"stream":False}
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+MODEL,
      data=json.dumps(payload,ensure_ascii=False).encode(),method="POST",
      headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"})
    with urlopen(req,timeout=125) as f:provider=json.load(f)
    if not isinstance(provider,dict) or provider.get("success") is False:raise ValueError("PROVIDER_FAIL")
    body=provider.get("result",provider)
    text=body.get("response") if isinstance(body,dict) else None
    if not isinstance(text,str) and isinstance(body,dict):
        choices=body.get("choices")
        if isinstance(choices,list) and choices:
            text=choices[0].get("message",{}).get("content")
    if not isinstance(text,str):raise ValueError("NO_PROVIDER_RESPONSE")
    return provider,text
def filter_models(x,probe):
    choices=probe["signatures"][TEST]
    expected=x["expected"]
    kept=sorted(choices) if expected in {"UNKNOWN","CONFLICT"} else sorted(k for k,v in choices.items() if v==expected)
    return {"first_test_survivors":sorted(probe["signatures"]["NO_ACCEPTED_ORDERS"]),
      "second_test_survivors_conditional_on_llm_premise":kept,
      "excluded_conditional":[x for x in sorted(choices) if x not in kept],
      "semantic_confirmation":"NOT_VERIFIED_BY_LINTER",
      "human_or_observational_confirmation_required":True}
def run(probes,out,execute):
    probe=read(probes)
    if probe["status"]!="PASS" or probe["best_discriminating_test"]!=TEST:
        raise ValueError("NO_VERIFIED_SECOND_TEST")
    cases=read(HERE/"cases.json")["cases"]
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if execute and not(account and token):raise SystemExit("MISSING_CLOUDFLARE_SECRETS")
    answers={}
    for case in cases:
        where=out/case["id"]
        msgs=messages(case,probe)
        save(where/"request_without_secrets.json",{"model":MODEL,"messages":msgs,"temperature":0,"max_tokens":700})
        record={"id":case["id"],"status":"PREPARED"}
        if execute:
            try:
                provider,raw=cloudflare(account,token,msgs)
                save(where/"provider_original.json",provider)
                (where/"llm_original.txt").write_text(raw,encoding="utf-8")
                review=parse(raw)
                check=validate(case,review)
                record={"id":case["id"],"review":review,"linter":check,
                  "original_sha256":hashlib.sha256(raw.encode()).hexdigest()}
                if check["status"]=="VALID_FORMAT":
                    record["outcome"]=filter_models(review,probe)
            except (HTTPError,URLError,TimeoutError,TypeError,ValueError,KeyError) as e:
                record={"id":case["id"],"status":"API_OR_PARSE_FAILURE","exception":type(e).__name__}
        answers[case["id"]]=record
        save(out/"records.json",answers)
        print("TRANSIT_CRITIC",json.dumps({"id":case["id"],
          "status":record.get("linter",{}).get("status",record.get("status")),
          "retained":record.get("outcome",{}).get("second_test_survivors_conditional_on_llm_premise")}),flush=True)
    if execute:
        gold=read(HERE/"gold.json")["labels"]
        scores=[{"id":cid,"expected":gold[cid],
          "actual":r.get("review",{}).get("expected") if r.get("linter",{}).get("status")=="VALID_FORMAT" else "INVALID",
          "retained":r.get("outcome",{}).get("second_test_survivors_conditional_on_llm_premise")} for cid,r in answers.items()]
        score={"n":len(scores),"correct":sum(r["expected"]==r["actual"] for r in scores),
          "rows":scores,"limitations":"Synthetic project-authored cases, no empirical enterprise data; semantic truth of LLM assertions unverified; two molecule graphs, not a general system search engine."}
        save(out/"score.json",score)
        print("TRANSIT_CRITIC_SCORE",json.dumps({"n":score["n"],"correct":score["correct"]}),flush=True)
def main():
    p=argparse.ArgumentParser()
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--execute",action="store_true")
    group.add_argument("--prepare-only",action="store_true")
    p.add_argument("--probes",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    run(a.probes,a.out,a.execute)
if __name__=="__main__":main()

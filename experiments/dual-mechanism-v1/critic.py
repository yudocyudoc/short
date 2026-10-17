#!/usr/bin/env python3
"""Real Llama as qualitative constraint critic; never designs graphs or equations.

Independent deterministic generator + OpenModelica calculate signatures first.
LLM assesses availability of three facts-based observations. Model pruning is
conditional on that unverified semantic interpretation, never an empirical truth.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from analyze import TESTS,next_experiment
HERE=Path(__file__).resolve().parent
MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
STATUSES={"LAG","SYNC","UNKNOWN","CONFLICT"}
SYSTEM="""Eres crítico semántico causal, NO constructor de modelos. Una máquina ya
enumeró cuatro grafos físicamente diferentes y OpenModelica calculó sus
resultados. Sólo interpretas hechos sobre tres comparaciones observacionales:
OBSERVED_VS_DISPATCH: tasa MOSTRADA en el tablero vs ritmo de despacho.
PHYSICAL_VS_DISPATCH: ritmo real de RECEPCIÓN FÍSICA vs despacho.
OBSERVED_VS_PHYSICAL: tasa MOSTRADA vs recepción física.
SYNC significa que son simultáneas SIN suavizado ni transporte intermedio.
LAG significa que una de esas cantidades cambia con retardo frente a otra.
UNKNOWN significa que los hechos no determinan la relación;
CONFLICT significa dos afirmaciones operativas incompatibles vigentes.
¡No confundas TRANSPORTE FÍSICO con filtro informacional de reporte!
La tasa mostrada no es lo mismo que el contador contable de eventos; aquí
REPORT_FILTER suaviza la MEDICIÓN de tasa, no retrasa transacciones individuales.
Si sólo hay registro de salida y tablero, NO inventes fecha de recepción.
Si falta una medida, usa UNKNOWN. Si alguna está en conflicto, indica CONFLICT.
Tus inferencias NO se consideran verdades hasta contrastarlas con observaciones.
No produzcas ecuaciones, números, Modelica, enlaces, porcentajes ni nombres
de grafos seleccionados. No copies ni inventes citas textuales: enlaza IDs.
Devuelve sólo JSON sin Markdown, con EXACTAMENTE:
{"case_id":"D01",
 "tests":{"OBSERVED_VS_DISPATCH":"LAG",
          "PHYSICAL_VS_DISPATCH":"LAG",
          "OBSERVED_VS_PHYSICAL":"SYNC"},
 "fact_ids":{"OBSERVED_VS_DISPATCH":["F1"],
             "PHYSICAL_VS_DISPATCH":["F1","F2"],
             "OBSERVED_VS_PHYSICAL":["F3"]},
 "next_question":""}
Cada dimensión declarada SYNC, LAG o CONFLICT requiere hechos existentes;
CONFLICT al menos dos hechos. Si hay incertidumbre añade una pregunta corta
y concreta sobre qué señal podría observarse para distinguir las opciones."""
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def parse(raw):
    text=raw.strip();mark=chr(96)*3
    if text.startswith(mark):
        m=re.fullmatch(re.escape(mark)+r"(?:json)?\s*([\s\S]*?)\s*"+re.escape(mark),text)
        if not m:raise ValueError("INVALID_SINGLE_FENCE")
        text=m.group(1).strip()
    obj=json.loads(text)
    if not isinstance(obj,dict):raise ValueError("JSON_NOT_OBJECT")
    return obj
def validate(case,proposal):
    issues=[]
    if not isinstance(proposal,dict) or set(proposal)!={"case_id","tests","fact_ids","next_question"}:
        return {"status":"INVALID","issues":["WRONG_SCHEMA"],"semantic_verified":False}
    if proposal["case_id"]!=case["id"]:issues.append("WRONG_CASE")
    results=proposal["tests"];refs=proposal["fact_ids"]
    if not isinstance(results,dict) or set(results)!=set(TESTS):
        issues.append("INVALID_TEST_SET");results={}
    if not isinstance(refs,dict) or set(refs)!=set(TESTS):
        issues.append("INVALID_REFERENCE_SET");refs={}
    available={f["id"] for f in case["facts"]}
    for test in TESTS:
        status=results.get(test)
        evidence=refs.get(test)
        if status not in STATUSES:issues.append("INVALID_STATUS_"+test)
        if not isinstance(evidence,list) or any(not isinstance(x,str) or x not in available for x in evidence) or len(evidence)!=len(set(evidence)):
            issues.append("BAD_FACT_IDS_"+test);continue
        if status in ("LAG","SYNC") and not evidence:issues.append("NO_POSITIVE_EVIDENCE_"+test)
        if status=="CONFLICT" and len(evidence)<2:issues.append("NO_COUNTEREVIDENCE_"+test)
    question=proposal["next_question"]
    if not isinstance(question,str) or len(question)>600:
        issues.append("INVALID_QUESTION")
    elif "UNKNOWN" in results.values() or "CONFLICT" in results.values():
        if not question.strip():issues.append("QUESTION_REQUIRED")
    return {"status":"VALID_FORMAT" if not issues else "INVALID","issues":issues,
      "semantic_verified":False}
def apply(proposal,signatures):
    possible=sorted(next(iter(signatures.values())))
    # Contradiction blocks irreversible pruning. Other readings may be
    # useful as hypotheses but are not allowed to override a known conflict.
    vals=proposal["tests"]
    if "CONFLICT" in vals.values():
        surviving=possible
        blocked="CONFLICT"
    else:
        surviving=[c for c in possible if all(
            vals[t] in ("UNKNOWN",signatures[t][c]) for t in TESTS)]
        blocked=None
    known=[t for t in TESTS if vals[t] in ("SYNC","LAG")]
    request=next_experiment(signatures,surviving,known)
    return {"survivors_conditional_on_critic_premises":surviving,
      "eliminated_conditionally":[x for x in possible if x not in surviving],
      "conflict_blocked_pruning":bool(blocked),
      "next_measurement_to_collect_if_observable":request,
      "next_measurement_available_in_real_business":"NOT_VERIFIED",
      "critic_question":proposal["next_question"],
      "evidence_semantics":"NOT_VERIFIED_BY_LINTER"}
def messages(case,signals):
    options=[{"graph":name,"signals":{t:signals[t][name] for t in TESTS}}
             for name in sorted(next(iter(signals.values())))]
    return [{"role":"system","content":SYSTEM},
      {"role":"user","content":json.dumps({"case":case,
         "candidate_signatures_from_openmodelica":options,
         "test_definitions":{
           "OBSERVED_VS_DISPATCH":"Reported delivery rate relative to dispatch",
           "PHYSICAL_VS_DISPATCH":"Physical customer receipt rate relative to dispatch",
           "OBSERVED_VS_PHYSICAL":"Reported rate relative to physical customer receipt"},
         "task":"Infer the qualitative constraints justified by the case, not a preferred model. Missing actual signals imply UNKNOWN."},ensure_ascii=False)}]
def call(account,token,msgs):
    payload={"messages":msgs,"stream":False,"temperature":0,"max_tokens":1100}
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+MODEL,
       data=json.dumps(payload,ensure_ascii=False).encode(),method="POST",
       headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
    with urlopen(req,timeout=125) as f:provider=json.load(f)
    if not isinstance(provider,dict) or provider.get("success") is False:
        raise ValueError("PROVIDER_FAILED")
    body=provider.get("result",provider)
    raw=body.get("response") if isinstance(body,dict) else None
    if not isinstance(raw,str) and isinstance(body,dict):
        choices=body.get("choices")
        if isinstance(choices,list) and choices:
            raw=choices[0].get("message",{}).get("content")
    if not isinstance(raw,str):raise ValueError("NO_RESPONSE")
    return provider,raw
def run(probe_file,out,execute):
    probe=read(probe_file)
    if probe["status"]!="PASS" or not probe["all_four_joint_signatures_distinct"]:
        raise ValueError("NO_REAL_MODEL_SIGNATURES")
    signal=probe["signatures"]
    cases=read(HERE/"cases.json")["cases"]
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if execute and not(account and token):raise SystemExit("NO_CLOUDFLARE_SECRETS")
    original={}
    for case in cases:
        folder=out/case["id"]
        msgs=messages(case,signal)
        save(folder/"request_without_secrets.json",
             {"model":MODEL,"temperature":0,"max_tokens":1100,"messages":msgs})
        result={"case_id":case["id"],"status":"PREPARED_ONLY"}
        if execute:
            try:
                provider,raw=call(account,token,msgs)
                save(folder/"provider_original.json",provider)
                (folder/"original_llm.txt").write_text(raw,encoding="utf-8")
                proposal=parse(raw)
                lint=validate(case,proposal)
                result={"case_id":case["id"],"proposal":proposal,"linter":lint,
                  "raw_sha256":hashlib.sha256(raw.encode()).hexdigest()}
                if lint["status"]=="VALID_FORMAT":
                    result["conditional_pruning"]=apply(proposal,signal)
            except (HTTPError,URLError,TimeoutError,ValueError,TypeError,KeyError) as e:
                result={"case_id":case["id"],"status":"PROVIDER_OR_PARSER_ERROR",
                        "exception_class":type(e).__name__}
        original[case["id"]]=result
        save(out/"results.json",original)
        print("IGC_DUAL_CRITIC_CASE",json.dumps({"id":case["id"],
          "admission":result.get("linter",{}).get("status",result.get("status")),
          "kept":result.get("conditional_pruning",{}).get("survivors_conditional_on_critic_premises")}),flush=True)
    if execute:
        gold=read(HERE/"gold.json")["labels"]
        rows=[]
        for case in cases:
            cid=case["id"];item=original[cid]
            recognized=item.get("proposal",{}).get("tests",{})
            accepted=item.get("linter",{}).get("status")=="VALID_FORMAT"
            rows.append({"id":cid,"admitted":accepted,
              "critic_all_three_match":accepted and recognized==gold[cid],
              "expected":gold[cid],
              "review":recognized if accepted else "NOT_ADMITTED",
              "preserved":item.get("conditional_pruning",{}).get("survivors_conditional_on_critic_premises")})
        score={"n":len(rows),"strict_three_test_matches":sum(x["critic_all_three_match"] for x in rows),
               "admitted":sum(x["admitted"] for x in rows),
               "cases":rows,
               "limitation":"8 synthetic cases by same team; no human-reviewed actual observations; contingent pruning, not formal validation"}
        save(out/"score.json",score)
        print("IGC_DUAL_CRITIC_FINAL",json.dumps({"correct":score["strict_three_test_matches"],
                "admitted":score["admitted"],"n":score["n"]}),flush=True)
def main():
    p=argparse.ArgumentParser()
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only",action="store_true")
    mode.add_argument("--execute",action="store_true")
    p.add_argument("--probes",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    run(x.probes,x.out,x.execute)
if __name__=="__main__":main()

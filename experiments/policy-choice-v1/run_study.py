#!/usr/bin/env python3
"""Frozen 12-case real Llama vs type-only and lexical baselines.
Policy macro selection only; not arbitrary topology synthesis."""
from __future__ import annotations
import argparse,hashlib,json,os,re
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
import compose
HERE=Path(__file__).resolve().parent
MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
SYSTEM="""Eres arquitecto de dinámica de sistemas. Dos mecanismos distintos MTO y MTS tienen PUERTOS EXTERNOS IDENTICOS, de modo que debes elegir usando la política causal de los hechos, no los tipos. MTO: cada objeto se prepara después de aceptar pedido; trabajos pendientes de preparación y trabajos terminados pendientes de entrega. MTS: se produce según plan independiente de pedidos, se acumula inventario terminado para enviar pedidos. Si no hay información sobre esa política, ABSTAIN y unresolved con EVIDENCE_MISSING. Si hay afirmaciones incompatibles del mismo producto y periodo, ABSTAIN y unresolved con CONFLICTING_POLICIES. Nunca completes hechos ausentes. No escribas fórmulas, números, parámetros ni Modelica. Devuelve JSON PURO con las claves EXACTAS decision,policy,instances,links,support,counterevidence,unresolved. decision: COMPOSE, ABSTAIN o PARTIAL; policy: MTO, MTS o null. Si COMPOSE: instances debe tener exactamente source con module SOURCE, un proceso con module MTO o MTS, y terminal module SINK; cada elemento tiene id, module, evidence; evidence es objeto fact_id y quote con cita literal exacta de por lo menos 24 caracteres. links conecta source.out a proceso.in y proceso.out a terminal.in; cada link tiene from, to, evidence literal. Incluye en support una cita positiva de la política y en counterevidence una cita que excluye o contradice a la rival. unresolved debe ser []. Si ABSTAIN usa policy:null, instances:[], links:[], support:[], counterevidence:[] y unresolved:["EVIDENCE_MISSING"] o ["CONFLICTING_POLICIES"], según hechos. No generes estructuras por obligación. JSON sin texto adicional."""
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def parse(raw):
    s=raw.strip()
    if s.startswith(chr(96)):
        marker=chr(96)*3
        m=re.fullmatch(re.escape(marker)+r"(?:json)?\s*([\s\S]*?)\s*"+re.escape(marker),s)
        if not m:raise ValueError("BAD_CODE_FENCE")
        s=m.group(1).strip()
    obj=json.loads(s)
    if not isinstance(obj,dict):raise ValueError("NOT_JSON_OBJECT")
    return obj
def msgs(case,history):
    cat=compose.read("catalog.json")
    seen={k:v for k,v in cat.items() if k!="backend"}
    out=[{"role":"system","content":SYSTEM},{"role":"user","content":json.dumps({"facts":case,"catalog":seen},ensure_ascii=False)}]
    for raw,diagnostic in history:
        out.extend([{"role":"assistant","content":raw},{"role":"user","content":json.dumps({"compiler_diagnostic":diagnostic,"instruction":"Repair only syntax, typed ports or citations. Never invent facts or write equations."},ensure_ascii=False)}])
    return out
def call(account,token,messages):
    body={"messages":messages,"stream":False,"temperature":0,"max_tokens":2400}
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+MODEL,method="POST",
                headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},
                data=json.dumps(body,ensure_ascii=False).encode())
    with urlopen(req,timeout=150) as h:provider=json.load(h)
    if not isinstance(provider,dict) or provider.get("success") is False:raise ValueError("PROVIDER_FAILED")
    obj=provider.get("result",provider)
    raw=obj.get("response") if isinstance(obj,dict) else None
    if not isinstance(raw,str) and isinstance(obj,dict):
        choices=obj.get("choices")
        if isinstance(choices,list) and choices:raw=choices[0].get("message",{}).get("content")
    if not isinstance(raw,str):raise ValueError("MISSING_MODEL_CONTENT")
    return provider,raw
def type_baseline(case):return "INSUFFICIENT_EVIDENCE"
def lex_baseline(case):
    text=" ".join(f["text"].lower() for f in case["facts"])
    mto=any(s in text for s in ("únicamente después","solo después","sólo después","no se imprime ningún","nunca trabaja sin"))
    mts=any(s in text for s in ("programa de fabricación","producción programada","calendario interno","inventario disponible antes"))
    if mto and mts:return "CONTRADICTORY"
    if mto:return "MTO"
    if mts:return "MTS"
    return "INSUFFICIENT_EVIDENCE"
def label(proposal):
    if not isinstance(proposal,dict):return "INVALID"
    if proposal.get("decision")=="COMPOSE":return proposal.get("policy") if proposal.get("policy") in ("MTO","MTS") else "INVALID"
    if proposal.get("decision")=="ABSTAIN":
        notes=proposal.get("unresolved",[])
        if isinstance(notes,list):
            if any("CONFLICTING_POLICIES" in str(x) for x in notes):return "CONTRADICTORY"
            if any("EVIDENCE_MISSING" in str(x) for x in notes):return "INSUFFICIENT_EVIDENCE"
    return "INVALID"
def evaluate(records):
    gold=compose.read("evaluation_gold.json")["cases"]
    rows=[]
    for c in compose.read("cases.json")["cases"]:
        cid=c["id"];expected=gold[cid]["policy"] or gold[cid]["status"]
        pred=label(records.get(cid,{}).get("accepted_proposal"))
        rows.append({"id":cid,"expected":expected,"llm":pred,
          "llm_compiler_status":records.get(cid,{}).get("accepted_status","NO_ACCEPTED_PROPOSAL"),
          "type_baseline":type_baseline(c),"lexical_baseline":lex_baseline(c),
          "llm_correct":pred==expected,"type_correct":type_baseline(c)==expected,
          "lexical_correct":lex_baseline(c)==expected,
          "attempt_count":len(records.get(cid,{}).get("attempts",[]))})
    return {"n":len(rows),"scores":{k:sum(r[k] for r in rows) for k in ("llm_correct","type_correct","lexical_correct")},
      "cases":rows,"warning":"12 synthetic project-authored cases and gold. No independent human evaluation, no claim of statistical generalization. Macro selection is not open-ended molecule composition."}
def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prepare-only",action="store_true")
    g.add_argument("--execute",action="store_true")
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--max-attempts",type=int,default=2)
    args=p.parse_args()
    if args.max_attempts<1 or args.max_attempts>3:raise ValueError("MAX_ATTEMPTS_1_TO_3")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","");token=os.getenv("CLOUDFLARE_API_TOKEN","")
    if args.execute and not(account and token):raise SystemExit("CLOUDFLARE_SECRETS_UNAVAILABLE")
    records={}
    for c in compose.read("cases.json")["cases"]:
        cid=c["id"];history=[];record={"attempts":[]}
        for attempt in range(1,args.max_attempts+1):
            folder=args.out/cid/("attempt_"+str(attempt))
            messages=msgs(c,history)
            save(folder/"request_without_secrets.json",{"model":MODEL,"messages":messages,"temperature":0,"max_tokens":2400})
            if not args.execute:break
            entry={"attempt":attempt,"prompt_hash":sha(json.dumps(messages,ensure_ascii=False))}
            raw=None
            try:
                provider,raw=call(account,token,messages)
                save(folder/"provider_original.json",provider)
                (folder/"original.txt").write_text(raw,encoding="utf-8")
                proposal=parse(raw)
                result=compose.validate(cid,proposal)
                save(folder/"typed_diagnostic.json",result)
                entry.update({"raw_hash":sha(raw),"checker":result["status"]})
                if result["status"] in ("STRUCTURALLY_VALID","ABSTAIN","PARTIAL"):
                    record["accepted_proposal"]=proposal
                    record["accepted_status"]=result["status"]
                    if result["executable"]:
                        code=compose.render(cid,proposal)
                        (folder/"IGCSelected.mo").write_text(code,encoding="utf-8")
                        record["rendered_code_sha256"]=sha(code)
                    record["attempts"].append(entry)
                    break
                history.append((raw,{"issues":result["issues"],"status":result["status"]}))
            except (HTTPError,URLError,TimeoutError,ValueError,KeyError,TypeError) as exc:
                entry["error_type"]=type(exc).__name__
                if raw is not None:history.append((raw,{"status":"INVALID_JSON","issues":[{"code":"RETURN_JSON_ONLY"}]}))
            record["attempts"].append(entry)
            save(folder/"attempt_info.json",entry)
        records[cid]=record
        save(args.out/"manifest.json",{"study":"IGC_MTO_MTS_CHOICE_V1","actual_model_calls":args.execute,"results":records})
        print("POLICY_CASE",json.dumps({"id":cid,"result":record.get("accepted_status","NO_PASS"),
             "prediction":label(record.get("accepted_proposal"))}),flush=True)
    result=evaluate(records) if args.execute else {"status":"PREPARED_ONLY","n":12}
    save(args.out/"evaluation.json",result)
    print("POLICY_STUDY_FINAL",json.dumps(result.get("scores",result)),flush=True)
if __name__=="__main__":main()

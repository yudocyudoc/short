#!/usr/bin/env python3
"""Independent model-as-reviewer benchmark: Qwen generates; GLM labels; Llama B/C tested.
Never assert machine proxy labels constitute human-validated causal ground truth.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,re,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

HERE=Path(__file__).resolve().parent
PILOT=HERE.parent/"evidence-molecules-pilot-v1"
sys.path.insert(0,str(PILOT))
import evaluate as old_eval
import deterministic as old_base
import run_llm as old_prompt

CFG=json.loads((HERE/"design.json").read_text(encoding="utf-8"))
FROZEN={
"run_llm.py":"7ccd118871987194e597175f2aa27653e509eb8b",
"deterministic.py":"c0ab9d8e6cfd5b1c3f28fb1081f66672e9721063",
"evaluate.py":"23ee7d08d10834c51143e4ecde1ddfe649d5b4c9",
"catalog_public.json":"18de84dad30a9627fc219676ae456168bd9da36f"}
def sha(x):return hashlib.sha256(x.encode("utf-8")).hexdigest()
def gitblob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def verify_frozen():
    for file,expected in FROZEN.items():
        if gitblob((PILOT/file).read_bytes())!=expected:raise RuntimeError("FROZEN_SOURCE_CHANGED:"+file)
    assert len(CFG["seeds"])==24
    assert len(set(x["id"] for x in CFG["seeds"]))==24
    assert CFG["tested_model"]==old_prompt.MODEL

GEN_SYSTEM="""Escribe una única viñeta CUALITATIVA ORIGINAL en español sobre la operación diaria de una organización. Tu papel es redactar hechos sintéticos para una evaluación externa; NO eres evaluador y no tienes acceso a etiquetas ni a respuestas de otro modelo. Escribe hechos que podrían sostener o no mecanismos dinámicos. Evita forzar que todas las viñetas tengan solución; pueden existir contradicciones, ausencia de información o mecanismos que no estén en catálogo. Utiliza lenguaje realista de personas de la empresa, sin tecnicismos de sistemas ni conceptos de ingeniería de software. No incluyas jamás cifras, fechas, cantidades, fórmulas, ecuaciones o códigos de mecanismo. Evita frases literales prefabricadas. Devuelve exclusivamente JSON válido con exactamente title, question, facts; facts es arreglo de tres o cuatro frases independientes. Ejemplo de estructura de respuesta, NO de contenido: {"title":"Nombre","question":"¿Qué mecanismos se justifican?","facts":["Hecho A de la operación.","Hecho B de la operación.","Hecho C de la operación."]}."""
REV_SYSTEM="""Eres un evaluador de Dinámica de Sistemas que debe definir etiquetas de referencia para un experimento. No conoces ni verás las predicciones de Llama. Tu tarea es elegir SOLO mecanismos positivamente sustentados por los hechos, según su contrato de uso, límites y exclusiones; no es completar un diagrama típico. Si la evidencia es insuficiente o contradictoria, selecciona cero mecanismos o indica INDETERMINATE según corresponda. No infieras una cola de trabajo sólo por un backlog de envíos, ni interpretes una demora administrativa como traslado físico de materiales, ni equipares capacidad de servicio o plantilla a utilización de capacidad industrial. Respeta que una molécula grande requiere TODOS sus requisitos estructurales: no la elijas sólo porque aparece una palabra familiar. Sin números, parámetros ni ecuaciones. Para cada mecanismo elegido aporta una cita exacta copiada de los hechos que lo respalda. No recibes ni produces respuestas de Llama.
Devuelve exclusivamente JSON válido con las cuatro claves siguientes: {"label_status":"DETERMINATE","molecules":["CAP_UTIL"],"support":[{"target":"CAP_UTIL","fact_id":"F1","quote":"fragmento literal exacto del hecho"}],"reason":"Explicación breve de por qué es apropiado o inapropiado cada mecanismo"}. label_status puede ser DETERMINATE o INDETERMINATE. Si INDETERMINATE, molecules y support deben ser arreglos vacíos. También puedes usar DETERMINATE con molecules=[] si el catálogo no contiene una molécula respaldada."""

def generate_messages(seed):
    return [{"role":"system","content":GEN_SYSTEM},{"role":"user","content":json.dumps(seed,ensure_ascii=False)}]
def review_messages(case):
    return [{"role":"system","content":REV_SYSTEM},{"role":"user","content":json.dumps({
       "question":case["question"],"facts":case["facts"],
       "available_molecules":old_prompt.CAT["molecules"]},ensure_ascii=False)}]

def parse(raw):
    t=raw.strip()
    ticks=chr(96)*3
    if t.startswith(ticks) and t.endswith(ticks):
        t=t[len(ticks):-len(ticks)].strip()
        if t.startswith("json"):t=t[4:].strip()
    v=json.loads(t)
    if not isinstance(v,dict):raise ValueError("NOT_OBJECT")
    return v

def parse_case(seed,raw):
    v=parse(raw)
    if set(v)!={"title","question","facts"}:raise ValueError("CASE_FIELDS")
    if not all(isinstance(v[k],str) and 5<=len(v[k])<=220 for k in ("title","question")):raise ValueError("CASE_METADATA")
    facts=v["facts"]
    if not isinstance(facts,list) or len(facts) not in (3,4):raise ValueError("CASE_FACT_COUNT")
    if not all(isinstance(f,str) and 28<=len(f)<=500 for f in facts):raise ValueError("CASE_FACT_LENGTH")
    if any(re.search(r"\d",f) for f in facts):raise ValueError("CASE_HAS_NUMBERS")
    if any(mid.lower() in " ".join(facts).lower() for mid in old_eval.MOLECULES):raise ValueError("CASE_HAS_LABEL")
    return {"id":seed["id"],"title":v["title"],"question":v["question"],
      "facts":[{"id":"F"+str(i+1),"text":f} for i,f in enumerate(facts)]}

def parse_reference(case,raw):
    v=parse(raw)
    if set(v)!={"label_status","molecules","support","reason"}:raise ValueError("REFERENCE_FIELDS")
    if v["label_status"] not in ("DETERMINATE","INDETERMINATE"):raise ValueError("REFERENCE_STATUS")
    if not isinstance(v["reason"],str) or not v["reason"].strip():raise ValueError("REFERENCE_REASON")
    mids=v["molecules"]; support=v["support"]
    if not isinstance(mids,list) or len(set(mids))!=len(mids) or not set(mids)<=old_eval.MOLECULES:
        raise ValueError("REFERENCE_MOLECULES")
    if not isinstance(support,list):raise ValueError("REFERENCE_SUPPORT")
    if v["label_status"]=="INDETERMINATE":
        if mids or support:raise ValueError("INDETERMINATE_NOT_EMPTY")
        return None
    evidence={m:set() for m in mids}
    facts={f["id"]:f["text"] for f in case["facts"]}
    for s in support:
        if not isinstance(s,dict) or set(s)!={"target","fact_id","quote"}:
            raise ValueError("REFERENCE_CITATION_FIELDS")
        if s["target"] not in evidence or s["fact_id"] not in facts or not isinstance(s["quote"],str):
            raise ValueError("REFERENCE_CITATION_REFERENCE")
        if len(s["quote"])<12 or s["quote"] not in facts[s["fact_id"]]:
            raise ValueError("REFERENCE_CITATION_NOT_LITERAL")
        evidence[s["target"]].add(s["fact_id"])
    if any(not v for v in evidence.values()):raise ValueError("REFERENCE_MISSING_POSITIVE_SUPPORT")
    return {"molecules":sorted(mids),"supported_facts":{k:sorted(v) for k,v in evidence.items()}}

def call(account,token,model,messages,limit,folder,phase):
    body={"messages":messages,"stream":False,"temperature":0,"max_tokens":limit}
    save(folder/"request.json",{"model":model,"body":body})
    meta={"phase":phase,"status":"PREPARED_ONLY","model":model,
          "prompt_hash":sha(json.dumps(messages,ensure_ascii=False))}
    if not (account and token):return meta,None
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/run/"+model,
      method="POST",headers={"Content-Type":"application/json","Authorization":"Bearer "+token},
      data=json.dumps(body,ensure_ascii=False).encode("utf-8"))
    try:
        with urlopen(req,timeout=150) as response:p=json.load(response)
        save(folder/"provider_original.json",p)
        raw=old_prompt.extract(p)
        (folder/"original.txt").write_text(raw,encoding="utf-8")
        meta.update({"status":"RECEIVED","original_sha256":sha(raw),"length":len(raw)})
        return meta,raw
    except HTTPError as e:meta.update({"status":"HTTP_ERROR","code":e.code})
    except (URLError,TimeoutError) as e:meta.update({"status":"TRANSPORT_ERROR","kind":type(e).__name__})
    except (ValueError,TypeError,KeyError) as e:meta.update({"status":"PROVIDER_RESPONSE_ERROR","kind":type(e).__name__})
    return meta,None

def phase_reference(out,account,token):
    status={"phase":"EXTERNAL_SOURCE_AND_REFERENCE","seeds":24,
       "tested_llama_calls":0,"generator":CFG["generator_model"],
       "reviewer":CFG["reviewer_model"],"entries":[]}
    cases=[];gold={};counts={}
    for seed in CFG["seeds"]:
        sid=seed["id"]
        folder=out/"reference"/"generator"/sid
        rec,raw=call(account,token,CFG["generator_model"],generate_messages(seed),1500,folder,"generator")
        rec["id"]=sid;status["entries"].append(rec)
        if raw is None:
            counts[sid]="NO_GENERATOR_RESPONSE";save(out/"reference"/"status.json",status);continue
        try:
            case=parse_case(seed,raw)
        except (ValueError,TypeError,KeyError) as e:
            counts[sid]="INVALID_GENERATOR:"+str(e);continue
        cases.append(case);save(folder/"parsed_case.json",case)
        folder=out/"reference"/"reviewer"/sid
        rec,raw=call(account,token,CFG["reviewer_model"],review_messages(case),1300,folder,"reviewer")
        rec["id"]=sid;status["entries"].append(rec)
        if raw is None:counts[sid]="NO_REVIEWER_RESPONSE";continue
        try:
            decision=parse_reference(case,raw)
            if decision is None:counts[sid]="REVIEWER_INDETERMINATE"
            else:
                gold[sid]=decision
                counts[sid]="LABELLED"
                save(folder/"parsed_reference.json",decision)
        except (ValueError,TypeError,KeyError) as e:
            counts[sid]="INVALID_REVIEWER:"+str(e)
        status["case_states"]=counts;save(out/"reference"/"status.json",status)
        print("EXTERNAL_REFERENCE_CASE",json.dumps({"id":sid,"status":counts[sid]}),flush=True)
    save(out/"reference"/"generated_cases.json",{"cases":cases})
    scored=[c for c in cases if c["id"] in gold]
    save(out/"reference"/"scored_cases.json",{"cases":scored})
    save(out/"reference"/"proxy_reference.json",{"cases":gold,"warning":"GLM auto-judged. Not human adjudicated."})
    status.update({"case_states":counts,"valid_generated":len(cases),
       "valid_references":len(scored),
       "excluded":24-len(scored),
       "gold_sha256":sha(json.dumps(gold,sort_keys=True)),
       "completed_before_llama":True})
    save(out/"reference"/"status.json",status)
    print("REFERENCE_FROZEN",json.dumps({k:status[k] for k in ("valid_generated","valid_references","excluded","gold_sha256")}),flush=True)
    return scored,gold,status

def phase_test(out,account,token,cases,gold,reference):
    old_eval.CASES={x["id"]:x for x in cases}
    old_eval.GOLD=gold
    responses={"deterministic":{c["id"]:old_base.respond(c) for c in cases},
               "generic_sd":{},"molecular_scaffold":{}}
    base=out/"tested"
    save(base/"baseline_original.json",responses["deterministic"])
    manifest={"phase":"FROZEN_LLAMA_EVALUATION","reference_sha256":reference["gold_sha256"],
      "tested_cases":len(cases),"entries":[],"frozen_sha":FROZEN}
    for index,case in enumerate(cases):
        for arm in (("generic_sd","molecular_scaffold") if index%2==0
                    else ("molecular_scaffold","generic_sd")):
            folder=base/arm/case["id"]
            rec,raw=call(account,token,old_prompt.MODEL,old_prompt.messages(case,arm),1250,folder,arm)
            rec["id"]=case["id"];manifest["entries"].append(rec)
            if raw is not None:responses[arm][case["id"]]=raw
            save(base/"manifest.json",manifest)
            print("BLIND_TEST_CALL",json.dumps({"case":case["id"],"arm":arm,"status":rec["status"]}),flush=True)
    for arm in responses:save(base/(arm+"_responses.json"),responses[arm])
    reports={arm:old_eval.summarize(responses[arm],arm) for arm in responses}
    b={x["case_id"]:x["strict_pass"] for x in reports["generic_sd"]["individual_cases"]}
    c={x["case_id"]:x["strict_pass"] for x in reports["molecular_scaffold"]["individual_cases"]}
    c_wins=sorted(k for k in b if not b[k] and c[k])
    b_wins=sorted(k for k in b if b[k] and not c[k])
    n=len(c_wins)+len(b_wins)
    p=min(1,2*sum(math.comb(n,k) for k in range(min(len(c_wins),len(b_wins))+1))/2**n) if n else 1
    score={"proxy_gold":"GLM labels of Qwen authored synthetic cases",
      "sample_size":len(cases),"original_seeds":24,
      "counts":{a:{k:v for k,v in r.items() if k!="individual_cases"} for a,r in reports.items()},
      "paired":{"scaffold_wins":c_wins,"generic_wins":b_wins,"discordant":n,
                "exact_mcnemar_p_exploratory":p},
      "details":{a:r["individual_cases"] for a,r in reports.items()},
      "limitations":["Automated proxy-reference is not independent human truth.",
        "Reviewer had the molecular contracts: proxy labels can favor scaffold arm.",
        "Cases and reference were generated by two independent AI families, not by external human field observers.",
        "Case exclusion on failed reviewer output was preregistered; report excluded cases.",
        "No numerical data or OpenModelica evaluation."]}
    save(base/"score.json",score)
    manifest["complete"]=sum(len(responses[x]) for x in ("generic_sd","molecular_scaffold"))==2*len(cases)
    manifest["summary"]=score["counts"];save(base/"manifest.json",manifest)
    print("BLIND_EVALUATION_COMPLETE",json.dumps({"n":len(cases),"score":score["counts"],
      "paired":score["paired"],"complete":manifest["complete"]}),flush=True)
    if account and not manifest["complete"]:raise SystemExit("INCOMPLETE_TEST_RESPONSES")
    return score

def main():
    a=argparse.ArgumentParser()
    group=a.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare-only",action="store_true")
    group.add_argument("--execute",action="store_true")
    a.add_argument("--out",required=True,type=Path)
    o=a.parse_args()
    verify_frozen()
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip() if o.execute else ""
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip() if o.execute else ""
    if o.execute and not (account and token):raise SystemExit("NO_CLOUDFLARE_CREDENTIALS")
    cases,gold,reference=phase_reference(o.out,account,token)
    if o.execute:
        if len(cases)<12:raise SystemExit("INSUFFICIENT_REVIEWED_CASES_BEFORE_ANY_LLAMA")
        phase_test(o.out,account,token,cases,gold,reference)
    else:print("PROMPT_PREPARATION_ONLY_NO_PAID_CALLS")

if __name__=="__main__":main()

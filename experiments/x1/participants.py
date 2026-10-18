#!/usr/bin/env python3
"""A: common-sense check; B: strong numeric optimizer; C: LLM conceptual critic.
No arm sees secret truth. No LLM writes Modelica, connectors, AST or equations.
"""
import argparse,json,os,math
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

ACTIONS=("none","upgrade_preparation","upgrade_distribution")
MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"

def load(p):return json.loads(Path(p).read_text())
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+"\n")

def model_call(system,data):
    acct=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    request_body={"messages":[{"role":"system","content":system},
                              {"role":"user","content":json.dumps(data,ensure_ascii=False)}],
                  "temperature":0,"max_tokens":700,"stream":False}
    result={"raw":None,"parsed":None,"error":None,"request_without_credentials":request_body}
    if not acct or not token:
        result["error"]="NO_CLOUDFLARE_CREDENTIALS";return result
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+acct+"/ai/run/"+MODEL,
                data=json.dumps(request_body).encode(),method="POST",
                headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
    try:
        with urlopen(req,timeout=145) as f: obj=json.load(f)
        raw=obj.get("result",{}).get("response")
        if obj.get("success") is False or not isinstance(raw,str):
            raise ValueError("BAD_PROVIDER_REPLY")
        result["raw"]=raw
        result["parsed"]=json.loads(raw)
    except (HTTPError,URLError,ValueError,TimeoutError,json.JSONDecodeError) as exc:
        result["error"]=type(exc).__name__
    return result

def expected_best(candidates):
    return {m:max(ACTIONS,key=lambda a:d["actions"][a]["net_units"]) for m,d in candidates.items()}

def matching(candidates,probe,value):
    if probe is None or value is None:return list(candidates)
    return [m for m,d in candidates.items() if abs(d["observables"][probe]-value)<=1e-4]

def action_for(candidates,models):
    if not models:return "abstain"
    best={expected_best(candidates)[m] for m in models}
    return next(iter(best)) if len(best)==1 else "abstain"

def choose_probe_B(candidates,allowed,probes):
    if not allowed:return None
    models=list(candidates)
    def reward(m,action):return candidates[m]["actions"][action]["net_units"]
    def average(a):return sum(reward(m,a) for m in models)/len(models)
    prior=max(average(a) for a in ACTIONS)
    gains={}
    for probe in allowed:
        total=0
        for m in models:
            obs=candidates[m]["observables"][probe]
            survivors=matching(candidates,probe,obs)
            a=max(ACTIONS,key=lambda act:sum(reward(z,act) for z in survivors)/len(survivors))
            total+=reward(m,a)
        gains[probe]=total/len(models)-probes[probe]["cost"]
    choice=max(gains,key=lambda k:gains[k])
    return choice if gains[choice]>prior+1e-6 else None

PICK_SYSTEM="""Eres asesora investigadora CEI/IGC; nunca escribas ni solicites AST o Modelica.
Examina dos mecanismos rivales de un negocio, sus costos y las observaciones disponibles.
Escoge UNA observación que pueda mejorar una decisión. Puedes abstenerte de medir.
No conoces cuál mecanismo es verdadero. Responde únicamente JSON exacto:
{"probe":"id_o_null","reason":"motivo breve","uncertainty":"qué no sabemos"}
Utiliza null auténtico si no propones observar. No inventes más probes ni nombres.
"""
ACT_SYSTEM="""Eres asesora investigadora CEI/IGC; no construyes grafos ni ecuaciones.
Mantén todas las hipótesis compatibles con la medición. Si recomiendan acciones
distintas y no hay más evidencia, abstente en vez de adivinar.
Devuelve JSON exacto, sin texto externo:
{"action":"none|upgrade_preparation|upgrade_distribution|abstain",
"survivors":["M_A"],"reason":"razón","uncertainty":"incertidumbre"}
Nunca afirme verdad estructural no observada.
"""

def select(initial,out):
    data=load(initial);cand=data["public_counterfactual_candidates"];dec={}
    for case in data["cases"]:
        cid=case["id"];allowed=case["allowed_probes"]
        answer=model_call(PICK_SYSTEM,{"problem":case["problem"],"description":case["observation"],
            "actions":case["actions"],"available_probes":[{"id":p,**data["probes"][p]} for p in allowed],
            "rival_consequences":cand})
        p=answer["parsed"]
        valid=(isinstance(p,dict) and set(p)=={"probe","reason","uncertainty"}
               and (p["probe"] is None or p["probe"] in allowed)
               and isinstance(p["reason"],str) and isinstance(p["uncertainty"],str))
        dec[cid]={
          "A":{"probe":"measure_departures" if "measure_departures" in allowed else None},
          "B":{"probe":choose_probe_B(cand,allowed,data["probes"])},
          "C":{"probe":p["probe"] if valid else None,"admission":"VALID" if valid else "INVALID",
               "raw_model":answer}
        }
    save(out,{"stage":"COMMITTED_BEFORE_PROBE","seal_sha256":data["seal_sha256"],"choices":dec})
    print("X1_PROBE_COMMIT",json.dumps({c:{k:v["probe"] for k,v in arms.items()} for c,arms in dec.items()}))

def decide(initial,choices,observed,out):
    data=load(initial);c=load(choices);o=load(observed)
    if len({data["seal_sha256"],c["seal_sha256"],o["seal_sha256"]})!=1:
        raise RuntimeError("SEAL_MISMATCH")
    rivals=data["public_counterfactual_candidates"];result={}
    for case in data["cases"]:
        cid=case["id"];result[cid]={}
        for arm in ("A","B","C"):
            probe=c["choices"][cid][arm]["probe"]
            value=o["cases"][cid][arm]["value"]
            survivors=matching(rivals,probe,value)
            choice=action_for(rivals,survivors)
            item={"probe":probe,"observation":value,"surviving_hypotheses":survivors,
                  "action":choice,"reason":"Conserva todos los rivales que reproducen la observación"}
            if arm=="C":
                answer=model_call(ACT_SYSTEM,{
                    "problem":case["problem"],"evidence":case["observation"],
                    "prior_probe":probe,"observed_value":value,
                    "survivors_calculated_from_models":survivors,
                    "candidate_counterfactuals":rivals,"action_budget":case["actions"]})
                p=answer["parsed"]
                valid=(isinstance(p,dict) and set(p)=={"action","survivors","reason","uncertainty"}
                       and p["action"] in (*ACTIONS,"abstain")
                       and isinstance(p["survivors"],list) and set(p["survivors"])==set(survivors)
                       and isinstance(p["reason"],str) and isinstance(p["uncertainty"],str))
                item.update({"action":p["action"] if valid else "abstain",
                             "reason":p["reason"] if valid else "INVALID_MODEL_DECISION",
                             "admission":"VALID" if valid else "INVALID","raw_model":answer})
            # Commit a numerical prediction *interval* before the reserved outcome is revealed.
            chosen=item["action"] if item["action"]!="abstain" else "none"
            item["predicted_deliveries_8h"]=[
                min(rivals[m]["actions"][chosen]["delivery_by_8h"] for m in survivors),
                max(rivals[m]["actions"][chosen]["delivery_by_8h"] for m in survivors)
            ] if survivors else None
            result[cid][arm]=item
    save(out,{"stage":"COMMITTED_BEFORE_HELDOUT","seal_sha256":data["seal_sha256"],"cases":result})
    print("X1_DECISION_COMMIT",json.dumps({
         k:{a:v["action"] for a,v in arms.items()} for k,arms in result.items()}))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--stage",choices=["choose","decide"],required=True)
    p.add_argument("--initial",type=Path,required=True)
    p.add_argument("--choices",type=Path)
    p.add_argument("--observed",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.stage=="choose":select(a.initial,a.out)
    else:decide(a.initial,a.choices,a.observed,a.out)

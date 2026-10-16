#!/usr/bin/env python3
"""Three independent LLM molecule-selection memos; no LLM JSON or generated equations.

The deterministic compiler judges each memo. This script does not fake success
when the model abstains or proposes an invalid composition.
"""
from __future__ import annotations
import argparse,hashlib,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError
from composer import compile_selection,load

MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
TEMP=.1
MAX_TOKENS=2500
CASE_IDS=("S1","S2","S3")
ROOT=Path(__file__).resolve().parent

INSTRUCTION="""Eres modelador de Dinámica de Sistemas. Recibes la pregunta de un negocio y un catálogo MUY LIMITADO de cuatro moléculas originales verificadas de Jim Hines.
Tu trabajo NO es inventar ecuaciones ni programar un modelo: debes seleccionar moléculas existentes y proponer una composición solo cuando representan el mecanismo pedido y sus interfaces son compatibles.
Puedes abstenerte y solicitar mediciones u otra molécula cuando la biblioteca no permita cerrar el mecanismo. No uses como sinónimos pedidos registrados al pagar, llegadas, demanda perdida o backlog de producción.
Los campos iniciales que siguen son SOLO la interfaz mínima para que un compilador pueda reconocer tu selección; el razonamiento debe ser prosa libre y sustantiva. NUNCA devuelvas JSON.
Formato:
ESTADO: ENSAMBLAR o ABSTENER
MOLECULAS: ID1, ID2 (o NINGUNA)
CONEXIONES: ID1.Puerto -> ID2.Puerto (o NINGUNA)
EXPLICACION:
Describe qué relación concreta representan y si falta un lazo. Incluye objeciones, no solo beneficios.
DATOS_FALTANTES:
Indica mediciones necesarias, y qué afirmaciones NO están justificadas.
No supongas que todas las preguntas son modelables con estas cuatro moléculas.
"""
def sha(text):return hashlib.sha256(text.encode("utf-8")).hexdigest()
def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")

def build_prompt(case,catalog):
    public={"case_id":case["case_id"],"title":case["title"],
            "question":case["question"],"facts":case["facts"]}
    # The compiler's private operational policy and simulation parameters are
    # not included in this prompt. No hidden oracle/answer labels supplied.
    return INSTRUCTION+"\nCATALOGO DISPONIBLE:\n"+json.dumps(catalog,ensure_ascii=False,indent=2,sort_keys=True)+ \
           "\n\nPROBLEMA:\n"+json.dumps(public,ensure_ascii=False,indent=2,sort_keys=True)

def get_response(wrapper):
    data=wrapper.get("result",wrapper)
    if isinstance(data,dict) and "response" in data:return data["response"],data.get("usage",{})
    if isinstance(data,dict) and isinstance(data.get("choices"),list) and data["choices"]:
        return data["choices"][0].get("message",{}).get("content"),data.get("usage",{})
    return data,{}

def run(out,execute):
    catalog=load("catalog.json")
    cases=load("cases_public.json")["cases"]
    if [c["case_id"] for c in cases]!=list(CASE_IDS):raise ValueError("CASE_LIST_CHANGED")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    if execute and (not account or not token):
        raise SystemExit("CLOUDFLARE_CREDENTIALS_MISSING: no requests performed")
    out.mkdir(parents=True,exist_ok=True)
    manifest={"experiment":"HINES_MOLECULE_COMPOSER_V1",
        "model":MODEL,"temperature":TEMP,"max_tokens":MAX_TOKENS,
        "max_calls":3,"revisions":0,"synthetic_training_claim":False,
        "started_utc":datetime.now(timezone.utc).isoformat(),"cases":[]}
    for case in cases:
        cid=case["case_id"];prompt=build_prompt(case,catalog)
        folder=out/cid
        body={"messages":[{"role":"user","content":prompt}],
              "stream":False,"temperature":TEMP,"max_tokens":MAX_TOKENS}
        write(folder/"request_without_secrets.json",{"model":MODEL,"body":body})
        info={"case_id":cid,"prompt_sha256":sha(prompt),"status":"PREPARED_ONLY"}
        if execute:
            url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}"
            request=Request(url,method="POST",
                            headers={"Authorization":f"Bearer {token}",
                                     "Content-Type":"application/json"},
                            data=json.dumps(body).encode("utf-8"))
            try:
                with urlopen(request,timeout=180) as response:provider=json.load(response)
                write(folder/"provider_original.json",provider)
                value,usage=get_response(provider)
                if isinstance(value,str):
                    (folder/"proposal_original.txt").write_text(value,encoding="utf-8")
                    compiled=compile_selection(cid,value)
                    write(folder/"compiled_plan.json",compiled)
                    info.update({"status":"COMPILED" if compiled["safe_to_simulate"] else compiled["status"],
                                 "compiler_reason":compiled.get("reason"),
                                 "api_success":provider.get("success",True),
                                 "response_sha256":sha(value),"usage":usage})
                else:
                    write(folder/"response_wrong_type.json",{"response":value})
                    info.update({"status":"NON_TEXT_RESPONSE","api_success":provider.get("success",True)})
            except HTTPError as e:info.update({"status":"HTTP_ERROR","http_code":e.code})
            except (URLError,TimeoutError) as e:
                info.update({"status":"TRANSPORT_ERROR","error_class":type(e).__name__})
        manifest["cases"].append(info)
        write(out/"manifest.json",manifest)
        print("MOLECULE_SELECTION",json.dumps(info,ensure_ascii=False),flush=True)
    manifest["finished_utc"]=datetime.now(timezone.utc).isoformat()
    write(out/"manifest.json",manifest)

def main():
    p=argparse.ArgumentParser()
    a=p.add_mutually_exclusive_group(required=True)
    a.add_argument("--dry-run",action="store_true")
    a.add_argument("--execute",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.out,args.execute)

if __name__=="__main__":main()

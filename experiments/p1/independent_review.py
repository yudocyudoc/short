#!/usr/bin/env python3
"""Single independent gold-free adversarial critique through Workers AI.
Invoked ONCE before P1 implementation; never given model results or expected labels.
"""
import json,os,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
BASE=Path(__file__).resolve().parent
MODEL="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
SYSTEM="""Actúa como segunda IA revisora independiente, hostil con los falsos PASS y
el overengineering de metodología SD, sin intención de complacer al constructor.
Solo juzga si la prueba P1 detectaría defectos reales antes de ampliar linter.
No construyas AST ni Modelica, no propongas cambiar de hoja de ruta.
No conoces gold ni respuesta numérica de mundos ocultos.
ATACA especialmente: una bifurcación legítima vs clonación de flujo, datos de
entidad diferentes con mismas unidades, un parámetro fijo disfrazado de feedback,
faltas de procedencia, correlación entre casos, falsas analogías de moléculas.
Inventar al menos UN contraejemplo nuevo, operativo y no contenido en Q1–Q5.
Identifica hallazgos específicos, severidad y qué prueba refutaría una mejora.
Salida: SOLO JSON con objeto:
{"verdict":"CONTINUE_P1|REPAIR_BRIEF|STOP","findings":[{"id":"R1","severity":"BLOCKS_P1|BLOCKS_P2|NON_BLOCKING","source":"Q1...|implementation|own_new","problem":"...","falsifying_case":"...","requested_fix":"..."}],"new_counterexample":{"description":"...","why_new":"...","expected_contract_behavior":"...","what_existing_engine_does":"... or UNKNOWN"},"limitations":["..."]}.
No inventes que corriste código ni que una clase ya fue admitida.
"""
def main():
    acct=os.environ.get("CLOUDFLARE_ACCOUNT_ID","").strip()
    token=os.environ.get("CLOUDFLARE_API_TOKEN","").strip()
    if not acct or not token:raise SystemExit("NO_PROVIDER_SECRETS")
    facts=json.loads((BASE/"review_input_no_gold.json").read_text())
    payload={"messages":[{"role":"system","content":SYSTEM},
                         {"role":"user","content":json.dumps(facts,ensure_ascii=False)}],
             "temperature":0,"stream":False,"max_tokens":2500}
    out=BASE/"audit_output";out.mkdir(parents=True,exist_ok=True)
    (out/"request_no_secrets.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2))
    req=Request("https://api.cloudflare.com/client/v4/accounts/"+acct+"/ai/run/"+MODEL,
       data=json.dumps(payload).encode(),method="POST",
       headers={"Content-Type":"application/json","Authorization":"Bearer "+token})
    try:
        with urlopen(req,timeout=145) as r:data=json.load(r)
    except HTTPError as exc:
        print("P1_REVIEW_PROVIDER_ERROR_HTTP",exc.code)
        raise
    body=data.get("result",{})
    raw=body.get("response") if isinstance(body,dict) else None
    if not isinstance(raw,str) and isinstance(body,dict):
        choices=body.get("choices",[])
        if choices:raw=choices[0].get("message",{}).get("content")
    if not isinstance(raw,str) or not raw.strip():raise RuntimeError("NO_MODEL_TEXT")
    (out/"original_response.txt").write_text(raw)
    try:
        obj=json.loads(raw)
    except json.JSONDecodeError:
        print("P1_REVIEW_NON_JSON_ORIGINAL_PRESERVED")
        raise
    if not isinstance(obj,dict) or not isinstance(obj.get("findings"),list) or not isinstance(obj.get("new_counterexample"),dict):
        raise RuntimeError("REVIEW_INVALID_SCHEMA_OR_MISSING_COUNTEREXAMPLE")
    (out/"review.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    print("P1_INDEPENDENT_CRITIQUE",json.dumps({"verdict":obj.get("verdict"),
          "n_findings":len(obj["findings"]),
          "counterexample_present":bool(obj["new_counterexample"].get("description")),
          "no_world_gold":True}))
if __name__=="__main__":main()

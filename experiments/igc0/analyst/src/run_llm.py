#!/usr/bin/env python3
"""Optional bounded blind LLM analyst: reads only prepared public inputs.

No evaluator/oracle file paths, no generator code, no automated corrections.
No numeric projections unless a separately calibrated, audited run exists.

Usage: CLOUDFLARE_ACCOUNT_ID=... CLOUDFLARE_API_TOKEN=... \
  python src/run_llm.py --inputs output/inputs --out output/llm --case M01
"""
import argparse,hashlib,json,os,re,sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from igc import validate_model,diagram
from prepare import write,sha

MODEL='@cf/deepseek-ai/deepseek-r1-distill-qwen-32b'
PROMPT_SYSTEM='''Eres un analista IGC de Dinámica de Sistemas. Recibes únicamente evidencia pública, sin acceso a generador ni oráculo. Construye un modelo mínimo IGC: IDENTIFICAR stocks/pipes/fronteras y diferencias sustentables, GRAFICAR proponiendo el mismo grafo tipado que otro programa dibujará, CONTRASTAR con referencia factible, examinar acciones.

No confundas cohortes POS fulfilled con completados en ventana de servicio. No inventes retornos esperados o simulaciones numéricas. Si no hay un simulador calibrado con parámetros suficientes, scenario_projections debe ser []. Los parámetros declarados de la referencia no demuestran que el mundo virtual opere exactamente así. No diagnostiques causalidad de una cola solo con agregados. Ante varias explicaciones igualmente compatibles usa non_identifiable y solicita medida separadora; ante incertidumbre usa insufficient_data. Puede que NO exista desviación material. Entrega SOLO el JSON final (el proveedor podría envolverlo en <think>).

Contrato:
{
"case_id":"Mxx",
"stocks":[{"id":"str","unit":"str","initial":null,"initial_label":"OBSERVADO|CALIBRADO|DESCONOCIDO","initial_refs":[{"source_id":"str","sha256":"hex"}]}],
"pipes":[{"id":"str","from":"str","to":"str","unit_per_time":"str","capacity_source":{"source_id":"str","sha256":"hex"}|null,"mechanism":"str","evidence_refs":[{"source_id":"str","sha256":"hex"}],"epistemic":"OBSERVADO|CALIBRADO|INFERIDO|HIPÓTESIS|DESCONOCIDO"}],
"boundary":{"inside":["str"],"outside":["str"],"possible_omissions":["str"]},
"contrast":[{"pipe_or_mechanism_id":"str","type":"difference|possible_difference|none","evidence_refs":[{"source_id":"str","sha256":"hex"}],"epistemic":"OBSERVADO|INFERIDO|HIPÓTESIS|DESCONOCIDO","explanation":"str"}],
"identifiability":{"status":"identifiable|non_identifiable|no_material_deviation|insufficient_data","rival_mechanisms":["str"],"discriminating_measurement":"str"},
"actions":["no_delivery","open_full","open_offpeak_capped"],
"decision":{"choice":"abstain","reason":"str","assumptions":["str"]},
"scenario_projections":[],"unknowns":["str"]
}
Citation IDs/hash exactly as provided (do not invent evidence_refs). Label uncertainty honestly; distinguish observed from inferred. You may propose stock IDs freely (not restricted to a vocabulary).'''

def separate(text):
    # Apply strict R1 first-think separation; no extracting JSON from arbitrary prose.
    if isinstance(text,dict):return text,None,'native_object'
    if not isinstance(text,str):return None,None,'invalid_type'
    t=text.strip();reason=None;kind='plain'
    if '<think>' in t or '</think>' in t:
        m=re.fullmatch(r'<think>(.*?)</think>\s*(.+)',t,re.S)
        if not m or t.count('<think>')!=1 or t.count('</think>')!=1:
            return None,None,'invalid_think'
        reason,t=m.group(1),m.group(2).strip();kind='think'
    m=re.fullmatch(r'```(?:json)?\s*\n(.*?)\n```',t,re.S|re.I)
    if m:t=m.group(1);kind+='_fenced'
    try:
        obj=json.loads(t)
        return (obj if isinstance(obj,dict) else None),reason,kind
    except json.JSONDecodeError:return None,reason,'invalid_json'

def one(packet,out,account,token):
    model=MODEL
    url=f'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}'
    data={'messages':[{'role':'system','content':PROMPT_SYSTEM},
                      {'role':'user','content':json.dumps(packet,ensure_ascii=False,separators=(',',':'))}],
          'temperature':0.1,'max_tokens':4500,'stream':False}
    api=Request(url,method='POST',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},
                data=json.dumps(data).encode())
    with urlopen(api,timeout=240) as resp:
        response=json.load(resp)
    if not response.get('success',True):raise RuntimeError('Cloudflare inference response failed')
    result=response.get('result',response)
    value=result.get('response') if isinstance(result,dict) else result
    usage=result.get('usage',{}) if isinstance(result,dict) else {}
    if value is None and isinstance(result,dict) and result.get('choices'):
        value=result['choices'][0]['message']['content']
    path=out/packet['case_id'];path.mkdir(parents=True,exist_ok=True)
    if isinstance(value,str):(path/'raw_response.txt').write_text(value)
    else:write(path/'raw_response.json',value)
    obj,reason,kind=separate(value)
    if reason is not None:(path/'reasoning.txt').write_text(reason)
    if obj is not None:
        write(path/'proposed_model.json',obj)
        verdict=validate_model(obj,packet)
        if verdict['accepted']:
            (path/'diagram.mmd').write_text(diagram(obj))
    else:verdict={'accepted':False,'issues':[{'code':'FORMAT','reason':kind}]}
    write(path/'validation.json',verdict)
    write(path/'usage.json',{'provider':model,'usage':usage,'transport_kind':kind,
                              'input_sha256':sha(packet), 'prompt_sha256':hashlib.sha256(PROMPT_SYSTEM.encode()).hexdigest(),
                              'model_accepted':verdict['accepted']})
    return packet['case_id'],verdict['accepted'],kind

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--inputs',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--case',choices=[f'M{i:02}' for i in range(1,9)])
    args=ap.parse_args()
    acc=os.getenv('CLOUDFLARE_ACCOUNT_ID','').strip();tok=os.getenv('CLOUDFLARE_API_TOKEN','').strip()
    if not acc or not tok:raise SystemExit('Cloudflare credentials required; no calls were made')
    cases=[args.inputs/f'{args.case}.json'] if args.case else sorted(args.inputs.glob('M*.json'))
    for p in cases:
        packet=json.loads(p.read_text())
        try:print('RESULT',one(packet,args.out,acc,tok),flush=True)
        except (HTTPError,URLError,TimeoutError) as e:
            # No automated retry. Error may count as failure in later evaluation.
            write(args.out/packet['case_id']/'error.json',{'case':packet['case_id'],'error':type(e).__name__})
            print('ERROR',packet['case_id'],type(e).__name__,flush=True)
            break
if __name__=='__main__':main()

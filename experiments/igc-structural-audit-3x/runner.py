"""IGC-AUDIT-3X: six independent DeepSeek calls (A without probes; B with probes).
The reserved evaluator key is never loaded and must not be published here.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from probes import report

ROOT=Path(__file__).resolve().parent
MODEL='@cf/deepseek-ai/deepseek-r1-distill-qwen-32b'
TEMP=.1
MAX_TOKENS=3500
CASES=('BB01','W17','W18')
ARMS=('A','B')
COMMON='''Eres auditor independiente de un modelo dinámico candidato. Evalúa si la implementación, los datos y las afirmaciones soportan la DECISIÓN mencionada. NO supongas que existe un error: un caso podría no contener fallas estructurales. No te preocupes por estilo de código ni bibliografía; enfócate en estructura, correspondencia con hechos, límites y significado de variables. Si hay múltiples hallazgos independientes, repórtalos por separado. Explica precisamente qué ecuación, frontera, dato o parámetro los produce. Una identidad de conservación o una simulación reproducible no prueban validez externa. No trates hipótesis como observaciones. No tienes acceso a otros casos de esta evaluación. No hay retroalimentación ni oportunidad de corregir una respuesta anterior. Tu respuesta será evaluada por un examinador independiente con criterios fijados antes de recibirla.

Devuelve un único objeto JSON, sin Markdown ni texto externo, con estas claves: case_id, decision_supported (YES/NO/CONDITIONAL), findings (array de objetos: locus, claim, mechanism, consequence, discriminating_test, confidence de 0 a 1), proposed_next_observation, what_is_not_identified, confidence (0 a 1). Si no encuentras una falla demostrable, di eso explícitamente y separa límites de evidencia de defectos de estructura. No inventes resultados observados.
'''

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def sha_bytes(data):return hashlib.sha256(data).hexdigest()

def prompt(case,arm):
    p=COMMON+'\nCASO PARA AUDITAR:\n'+json.dumps(case,ensure_ascii=False,sort_keys=True,indent=2)
    if arm=='B':
        p+='\n\nRESULTADOS DE HERRAMIENTAS ARITMÉTICAS INDEPENDIENTES (no contienen diagnóstico ni veredicto):\n'
        p+=json.dumps(report(case),ensure_ascii=False,sort_keys=True,indent=2)
    return p

def response_value(provider):
    v=provider.get('result',provider)
    if isinstance(v,dict) and 'response' in v:return v['response'],v.get('usage',{})
    if isinstance(v,dict) and v.get('choices'):
        return v['choices'][0].get('message',{}).get('content'),v.get('usage',{})
    return v,{}

def isolate_json(value):
    if isinstance(value,dict):return value,'provider_dict'
    if not isinstance(value,str):return None,'wrong_type'
    s=value.strip()
    if s.startswith('<think>') and '</think>' in s:
        if s.count('<think>')!=1 or s.count('</think>')!=1:
            return None,'bad_think_delimiters'
        s=s.split('</think>',1)[1].strip()
    fence=chr(96)*3
    if s.startswith(fence) and s.endswith(fence):
        m=re.fullmatch(re.escape(fence)+r'(?:json)?\s*\n(.*?)\n'+re.escape(fence),s,flags=re.S|re.I)
        if m:s=m.group(1)
    try: obj=json.loads(s)
    except ValueError:return None,'non_json'
    return (obj,'parsed_object') if isinstance(obj,dict) else (None,'not_object')

def run(out,do_execute):
    cases=json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))['cases']
    assert {c['case_id'] for c in cases}==set(CASES)
    account=os.getenv('CLOUDFLARE_ACCOUNT_ID','').strip()
    token=os.getenv('CLOUDFLARE_API_TOKEN','').strip()
    if do_execute and (not account or not token):raise SystemExit('Cloudflare secrets missing. No LLM calls performed.')
    manifest={'experiment':'IGC_STRUCTURE_AUDIT_3X_V1','run_started_utc':datetime.now(timezone.utc).isoformat(),
              'model':MODEL,'temperature':TEMP,'max_tokens':MAX_TOKENS,'max_calls':6,
              'blind_from_evaluator':True,'no_interaction_between_calls':True,'results':[]}
    url=f'https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{MODEL}' if do_execute else None
    for arm in ARMS:
        for cid in CASES:
            c=next(x for x in cases if x['case_id']==cid)
            text=prompt(c,arm)
            case_dir=out/f'{cid}-{arm}'
            body={'messages':[{'role':'user','content':text}],
                  'stream':False,'temperature':TEMP,'max_tokens':MAX_TOKENS}
            dump(case_dir/'request_without_secrets.json',{'model':MODEL,'request':body})
            info={'case_id':cid,'arm':arm,'prompt_sha256':sha_bytes(text.encode()),'status':'PREPARED_ONLY'}
            if do_execute:
                req=Request(url,method='POST',data=json.dumps(body).encode(),
                    headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'})
                try:
                    with urlopen(req,timeout=180) as res: provider=json.load(res)
                    dump(case_dir/'provider_original.json',provider)
                    value,usage=response_value(provider)
                    obj,format_result=isolate_json(value)
                    if isinstance(value,str):(case_dir/'response_original.txt').write_text(value,encoding='utf-8')
                    else:dump(case_dir/'response_original.json',value)
                    if obj is not None:dump(case_dir/'response_parsed.json',obj)
                    info.update({'status':'OK' if obj else 'FORMAT_REJECT','format':format_result,
                                 'api_success':provider.get('success',True),'usage':usage})
                except HTTPError as e:
                    info.update({'status':'HTTP_ERROR','http_code':e.code})
                except (URLError,TimeoutError) as e:
                    info.update({'status':'NETWORK_ERROR','exception':type(e).__name__})
            manifest['results'].append(info)
            dump(out/'manifest.json',manifest)
            print(json.dumps(info,ensure_ascii=False),flush=True)
    manifest['run_finished_utc']=datetime.now(timezone.utc).isoformat()
    dump(out/'manifest.json',manifest)
    if do_execute and any(x['status']!='OK' for x in manifest['results']):sys.exit(2)

def main():
    p=argparse.ArgumentParser();group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run',action='store_true')
    group.add_argument('--execute',action='store_true')
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();run(args.out,args.execute)

if __name__=='__main__':main()

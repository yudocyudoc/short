#!/usr/bin/env python3
"""Transparent keywords-only rules, operating strictly on the same public facts as both LLM arms."""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from evaluate import CASES,summarize

def contains(x,patterns): return any(re.search(p,x,re.I) for p in patterns)

def respond(case):
    fs=case['facts']; joined=' '.join(f['text'] for f in fs).lower()
    # Generic contradiction & incomplete-source stops; no case IDs or answer key.
    conflict=(contains(joined,[r'gerencia.*anticipadamente']) and contains(joined,[r'nunca se fabrican']))
    observed_only=contains(joined,[r's[oó]lo registra los pagos',r'no hay informaci[oó]n de clientes'])
    unsupported=contains(joined,[r'contrat',r'plantilla laboral',r'autorizaci[oó]n de una solicitud'])
    ruled_out=contains(joined,[r'no conserva pedidos pendientes',r'no hay transporte de material'])
    scored={}
    if not (conflict or observed_only or unsupported or ruled_out):
        def matched(patterns):
            for f in fs:
                if contains(f['text'].lower(),patterns):return f
            return None
        cap=matched([r'producci[oó]n deseada.*capacidad',r'capacidad.*producci[oó]n deseada',r'curva de utilizaci[oó]n.*capacidad'])
        if cap:scored['CAP_UTIL']=cap
        backlog=matched([r'pedidos confirmados pendientes.*despach',r'backlog.*despach',r'pedidos confirmados sin surtir',r'[oó]rdenes de compra confirmadas.*esperan',r'env[ií]o reduce.*inventario'])
        if backlog and contains(joined,[r'inventario',r'existencias',r'bodega',r'almac[eé]n']):scored['BACKLOG_FLOW']=backlog
        delay=matched([r'material.*en tr[aá]nsito',r'mercanc[ií]a.*viajando',r'despu[eé]s del traslado',r'viajando antes de entrar'])
        if delay:scored['MATERIAL_DELAY']=delay
        mto=matched([r's[oó]lo comienza despu[eé]s de aceptar',r's[oó]lo.*despu[eé]s de.*encargo',r'preparaci[oó]n.*pedidos aceptados'])
        if mto and contains(joined,[r'otra acumulaci[oó]n',r'esperan.*entreg',r'preparad.*entreg',r'mensajero']):scored['MTO_S2_PATTERN']=mto
    cites=[{'target':mid,'fact_id':f['id'],'quote':f['text']} for mid,f in sorted(scored.items())]
    if not scored:
        bad=next((f for f in fs if contains(f['text'],[r'no ',r's[oó]lo',r'sin ',r'desconocid',r'descripci[oó]n'])),fs[0])
        cites=[{'target':'ABSTAIN','fact_id':bad['id'],'quote':bad['text']}]
    return {'decision':'COMPOSE' if scored else 'ABSTAIN','molecules':sorted(scored),
            'citations':cites,'unresolved':[]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--score-out',type=Path,required=True)
    a=p.parse_args()
    result={cid:respond(case) for cid,case in CASES.items()}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    score=summarize(result,'deterministic')
    a.score_out.write_text(json.dumps(score,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DETERMINISTIC_BASELINE',json.dumps({k:v for k,v in score.items() if k!='individual_cases'}))
if __name__=='__main__':main()

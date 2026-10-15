#!/usr/bin/env python3
"""IGC-0 PUBLIC-ONLY evidence preparation; never loads an evaluator/oracle.

Usage: python src/prepare.py --public-zip IGC0_8_mundos_analista.zip --out output
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

ALLOWED = {'OBSERVADO','CALIBRADO','INFERIDO','SIMULADO','HIPÓTESIS','DESCONOCIDO'}
WINDOWS=('valle_am','pico','valle_pm')

def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def sha(obj):return hashlib.sha256(canonical(obj).encode('utf-8')).hexdigest()

def write(path, obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def check_record(rec):
    if rec['evidence_type'] not in ALLOWED:raise ValueError('Illegal epistemic label')
    if sha({k:v for k,v in rec.items() if k!='sha256'}) != rec['sha256']:
        raise ValueError('Source hash mismatch: '+rec.get('source_id','?'))
    return rec

def verify_typed_fields(x, key=None):
    if isinstance(x,dict):
        if {'value','unit','source_id','evidence_type','sha256'}.issubset(x):
            check_record_typed(x,key)
        for k,v in x.items():verify_typed_fields(v,k)
    elif isinstance(x,list):
        for v in x:verify_typed_fields(v)

def check_record_typed(x,key):
    # Original generator hashed a field before its sha256 was inserted.
    y={k:v for k,v in x.items() if k!='sha256'}
    if sha(y)!=x['sha256'] and sha({'metric':key,**y})!=x['sha256']:
        raise ValueError('Calibrated/source field hash mismatch: '+x['source_id']+':'+str(key))

def read_public(path):
    packs={}
    with ZipFile(path) as z:
        names=set(z.namelist())
        if any(n.startswith('holdout/') or n.startswith('src/') for n in names):
            raise ValueError('Analyst input contains evaluator or generator material')
        index=json.loads(z.read('public/index.json'))
        assert index['contains_ground_truth'] is False
        for item in index['cases']:
            cid=item['case_id'];name=f'public/{cid}/packet.json'
            packet=json.loads(z.read(name))
            if packet['case_id']!=cid or packet['packet_sha256']!=item['packet_sha256']:
                raise ValueError('Index/packet mismatch: '+cid)
            if sha({k:v for k,v in packet.items() if k!='packet_sha256'})!=packet['packet_sha256']:
                raise ValueError('Packet digest mismatch: '+cid)
            rows=packet['evidence']['pos_by_arrival_cohort']
            ledgers=packet['evidence']['daily_stock_finance_snapshots']
            if len(rows)!=42 or len(ledgers)!=14:raise ValueError('Missing window/closing observations')
            for row in rows+ledgers+packet['evidence']['operating_notes']:check_record(row)
            verify_typed_fields(packet['operating_reference'])
            ids=[r['source_id'] for r in rows+ledgers+packet['evidence']['operating_notes']]
            if len(ids)!=len(set(ids)):raise ValueError('Duplicate evidence source_id')
            packs[cid]=packet
    if len(packs)!=8:raise ValueError('Expected eight worlds')
    return packs

def abbreviated_reference(ref):
    def walk(o):
        if isinstance(o,dict) and {'value','unit','source_id','sha256','evidence_type'}.issubset(o):
            return {k:o[k] for k in ('value','unit','source_id','sha256','evidence_type')}
        if isinstance(o,dict):return {k:walk(v) for k,v in o.items()}
        if isinstance(o,list):return [walk(v) for v in o]
        return o
    return walk(ref)

def summarize(p):
    rows=p['evidence']['pos_by_arrival_cohort']
    daily=p['evidence']['daily_stock_finance_snapshots']
    bywin=defaultdict(lambda:defaultdict(int))
    cohort=[]
    for r in rows:
        v=r['values'];w=v['window'];d=v['day']
        safe={k:v[k] for k in v}
        cohort.append({'source_id':r['source_id'],'sha256':r['sha256'],'evidence_type':r['evidence_type'],**safe})
        for k,n in v.items():
            if k not in ('day','window'):bywin[w][k]+=n
    grand={k:sum(bywin[w][k] for w in WINDOWS) for k in bywin['pico']}
    # Do not equate arrival cohort outcomes with actual delivery window output.
    windows={w:dict(bywin[w]) for w in WINDOWS}
    ledger=[{'source_id':r['source_id'],'sha256':r['sha256'],'evidence_type':r['evidence_type'],**r['values']} for r in daily]
    last=ledger[-1]; cash_deficit=sum(r['cash_end_mxn']<0 for r in ledger)
    instore_rate=grand['presencial_fulfilled']/grand['presencial_accepted'] if grand['presencial_accepted'] else None
    delivery_cancel_rate=grand['delivery_canceled']/grand['delivery_accepted'] if grand['delivery_accepted'] else None
    typical={'instore_fulfill_fraction_cohort':instore_rate,
             'delivery_cancel_fraction_cohort':delivery_cancel_rate,
             'observed_cash_deficit_days':cash_deficit,
             'closing_inventory_meals':last['inventory_end'],
             'closing_cash_mxn':last['cash_end_mxn'],
             'closing_receivables_mxn':last['receivables_end_mxn']}
    ref=p['operating_reference']
    cap=ref['reference']['kitchen_capacity_per_hour'];hours=ref['windows'][0]['hours']
    # This is only a calibrated nominal bound, NOT available capacity in any actual window.
    nominal=cap['value']*hours['value']
    candidate={
        'metric':'reference_nominal_kitchen_capacity_per_window',
        'value':nominal,'unit':'orders/2h','label':'INFERIDO',
        'from':[{'source_id':cap['source_id'],'sha256':cap['sha256']},
                {'source_id':hours['source_id'],'sha256':hours['sha256']}],
        'warning':'Nominal reference, not observed or available per-window virtual capacity'
    }
    rows_audit=[{'source_id':r['source_id'],'sha256':r['sha256'],'kind':'OBSERVADO'} for r in rows+daily+p['evidence']['operating_notes']]
    return {
        'case_id':p['case_id'],
        'packet_sha256':p['packet_sha256'],
        'data_origin':p['data_origin'],
        'analysis_task':p['analysis_task'],
        'operating_reference':abbreviated_reference(ref),
        'pos_by_arrival_cohort':cohort,
        'daily_stocks':ledger,
        'operating_notes':p['evidence']['operating_notes'],
        'window_totals':windows,
        'horizon_totals':grand,
        'observed_decision_indicators':typical,
        'derived_reference_bounds':[candidate],
        'limitations':p['limitations'],
        'source_ledger':rows_audit,
        'epistemic':{
            'pos':'OBSERVADO','reference':'CALIBRADO','derived_capacity':'INFERIDO',
            'hypothesized_mechanisms':'HIPÓTESIS','counterfactual_without_model':'DESCONOCIDO'
        }
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--public-zip',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    cases=read_public(a.public_zip)
    manifest=[]
    for cid,p in cases.items():
        body=summarize(p)
        write(a.out/'inputs'/f'{cid}.json',body)
        manifest.append({'case_id':cid,'packet_sha256':p['packet_sha256'],
                         'input_sha256':sha(body),
                         'pos_rows':len(body['pos_by_arrival_cohort']),
                         'ledger_rows':len(body['daily_stocks'])})
    write(a.out/'input_manifest.json',{'cases':manifest,'blind':True,
           'no_oracle_loaded':True,'origin':'public package IGC0-8'})
    print(f'{len(manifest)} public cases verified; {sum(x["pos_rows"] for x in manifest)} POS rows')

if __name__=='__main__':main()

#!/usr/bin/env python3
"""Frozen pilot scoring. Literal anchoring is not semantic truth; labels are preregistered human judgments."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOLECULES = {m['id'] for m in json.loads((HERE/'catalog_public.json').read_text())['molecules']}
CASES = {c['id']: c for c in json.loads((HERE/'cases_public.json').read_text())['cases']}
GOLD = json.loads((HERE/'gold_private.json').read_text())['cases']
ARMS = ('deterministic', 'generic_sd', 'molecular_scaffold')

def error(code, case_id):
    return {'case_id':case_id, 'parsed':False, 'reason':code, 'selection_exact':False,
            'literal_quotes_valid':False, 'supported_citations':False, 'strict_pass':False,
            'unsupported_molecules':0}

def clean_response(raw):
    if isinstance(raw, dict):
        obj = raw
    elif isinstance(raw, str):
        # No markdown cleaning or correction. Compare literal LLM response to strict output contract.
        obj = json.loads(raw)
    else:
        raise ValueError('RESPONSE_NOT_OBJECT_OR_TEXT')
    if not isinstance(obj, dict) or set(obj) != {'decision','molecules','citations','unresolved'}:
        raise ValueError('SCHEMA_KEYS')
    decision, molecules, cites, missing = (obj['decision'],obj['molecules'],obj['citations'],obj['unresolved'])
    if decision not in ('COMPOSE','ABSTAIN') or not isinstance(molecules,list) or not all(isinstance(m,str) for m in molecules):
        raise ValueError('DECISION_OR_MOLECULE_SCHEMA')
    if len(molecules)!=len(set(molecules)) or not set(molecules).issubset(MOLECULES):
        raise ValueError('UNKNOWN_DUPLICATE_MOLECULE')
    if (decision == 'ABSTAIN') != (len(molecules)==0):
        raise ValueError('INCONSISTENT_ABSTENTION')
    if not isinstance(cites,list) or not isinstance(missing,list) or not all(isinstance(x,str) for x in missing):
        raise ValueError('CITATION_OR_UNRESOLVED_SCHEMA')
    if not cites or len(cites)>12:
        raise ValueError('MISSING_OR_EXCESS_CITATIONS')
    for item in cites:
        if not isinstance(item,dict) or set(item) != {'target','fact_id','quote'}:
            raise ValueError('CITATION_SCHEMA')
        if not all(isinstance(item[x],str) for x in ('target','fact_id','quote')):
            raise ValueError('CITATION_TYPE')
        if item['target'] not in set(molecules)|({'ABSTAIN'} if decision=='ABSTAIN' else set()):
            raise ValueError('UNEXPECTED_CITATION_TARGET')
    return obj

def assess(case_id, raw):
    if case_id not in CASES: raise KeyError(case_id)
    try: p = clean_response(raw)
    except (ValueError,TypeError,json.JSONDecodeError) as exc:
        return error(type(exc).__name__+':'+str(exc),case_id)
    goal = GOLD[case_id]
    expected = set(goal['molecules'])
    predicted = set(p['molecules'])
    facts = {f['id']:f['text'] for f in CASES[case_id]['facts']}
    checks = []
    supported = []
    target_has_literal={mid:False for mid in predicted}
    target_has_grounded={mid:False for mid in predicted}
    abstention_has_quote=False
    for cit in p['citations']:
        f = facts.get(cit['fact_id'])
        quote = cit['quote']
        valid = bool(f and quote.strip() and len(quote)>=12 and quote in f)
        checks.append(valid)
        if valid:
            if cit['target']=='ABSTAIN':abstention_has_quote=True
            elif cit['target'] in predicted:
                target_has_literal[cit['target']]=True
                if cit['fact_id'] in goal['supported_facts'].get(cit['target'],[]):
                    target_has_grounded[cit['target']]=True
    literal_ok = bool(all(checks) and (all(target_has_literal.values()) if predicted else abstention_has_quote))
    supports_ok = bool(literal_ok and (all(target_has_grounded.values()) if predicted else True))
    decision_correct = (p['decision']==('COMPOSE' if expected else 'ABSTAIN'))
    selection_exact = (predicted==expected and decision_correct)
    return {'case_id':case_id,'parsed':True,'decision':p['decision'],'selected':sorted(predicted),
       'expected':sorted(expected),'selection_exact':selection_exact,
       'literal_quotes_valid':literal_ok, 'supported_citations':supports_ok,
       'strict_pass':bool(selection_exact and supports_ok),
       'unsupported_molecules':len(predicted-expected),
       'false_abstention':bool(expected and p['decision']=='ABSTAIN'),
       'citation_results':checks,
       'reason': 'PASS' if selection_exact and supports_ok else 'SELECTION_OR_CITATION_FAILURE'}

def summarize(responses,arm):
    details=[]
    for cid in CASES:
        if cid not in responses:
            details.append(error('NO_ACTUAL_RESPONSE',cid))
        else:
            details.append(assess(cid,responses[cid]))
    return {'arm':arm,'evaluated':sum(x['parsed'] for x in details),'total':len(CASES),
            'exact_selection':sum(x['selection_exact'] for x in details),
            'literal_quote_pass':sum(x['literal_quotes_valid'] for x in details),
            'source_supported_citation_pass':sum(x['supported_citations'] for x in details),
            'strict_pass':sum(x['strict_pass'] for x in details),
            'unsupported_molecules':sum(x['unsupported_molecules'] for x in details),
            'false_abstentions':sum(x.get('false_abstention',False) for x in details),
            'individual_cases':details}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--responses',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--arm',choices=ARMS,required=True)
    a=ap.parse_args()
    raw=json.loads(a.responses.read_text(encoding='utf-8'))
    s=summarize(raw,a.arm)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('IGC_PILOT_SCORE',json.dumps({k:v for k,v in s.items() if k!='individual_cases'}))

if __name__=='__main__':main()

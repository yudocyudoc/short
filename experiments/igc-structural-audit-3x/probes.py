"""Independent deterministic probes for IGC structural audit.
Numerical calculations are not diagnoses or ground truth observations.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def interp(points, r):
    if r <= points[0][0]: return points[0][1]
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        if r <= x1: return y0+(r-x0)*(y1-y0)/(x1-x0)
    return points[-1][1]

def fluid_proxy(counts, cap):
    q = 0.0; maximum = 0.0
    for n in counts:
        q=max(0.0, q+n-cap/4)
        maximum=max(maximum,q)
    return {'end_of_24h':round(q,6), 'max_after_quarter_step':round(maximum,6)}

def stock_run(case, orders=None):
    purchase=case['purchase_orders_units_by_day'] if orders is None else orders
    demand=case['customer_demand_units_by_day']; i=case['initial_stock_units']; rows=[]
    delay=case['supplier_delivery_lag_days']
    for t in range(len(purchase)):
        if "purchase_orders[t-2] if t>=2" in case['candidate_implementation']:
            r=purchase[t-delay] if t>=delay else 0
        else:
            r=purchase[t]
        shipped=min(i+r,demand[t]); i=i+r-shipped
        rows.append({'day':t,'received_units':r,'shipped_units':shipped,'inventory_end':i})
    return rows

def check_ledger_mutations():
    examples=[]
    for mode, produced, shipped in [('original',10,8),('producing_times_3',30,8),('ship_without_stock_constraint',10,25)]:
        backlog_initial=5;inventory_initial=4;orders=12
        b_final=backlog_initial+orders-shipped
        i_final=inventory_initial+produced-shipped
        examples.append({'variant':mode,'orders':orders,'produced':produced,'shipped':shipped,
            'backlog_end':b_final,'prepared_stock_end':i_final,
            'backlog_conservation_residual':b_final-(backlog_initial+orders-shipped),
            'inventory_conservation_residual':i_final-(inventory_initial+produced-shipped)})
    return examples

def report(case):
    if case['case_id']=='BB01':
        lookup=case['equations_and_design']['lookup_points']
        grid=[0,.05,.125,.25,.5,.75,1,1.2]
        data={'case_id':case['case_id'], 'arithmetic_probes': {
            'lookup_samples':[{'desired_to_capacity':r, 'utilization':round(interp(lookup,r),6),
                               'ratio_of_production_to_desired':round(interp(lookup,r)/r,6) if r else None} for r in grid],
            'scenario_probes':[],
            'balance_mutations':check_ledger_mutations(),
            'notes': ['The fluid proxy assumes continuously available capacity, treating each POS count as an arrival for calculation only; it is not a fitted replacement model.',
                      'Balance mutations are algebraic examples, not original-Hines perturbations.']}}
        for day,counts in case['observed_sales_by_quarter_hour'].items():
            for cap in case['equations_and_design']['parameters']['capacity_orders_per_hour']:
                produced=sum(cap*interp(lookup,4*n/cap)*.25 for n in counts)
                data['arithmetic_probes']['scenario_probes'].append({
                    'day':day,'capacity':cap,'recorded_transactions':sum(counts),
                    'production_from_lookup_integral':round(produced,6),
                    'fluid_proxy':fluid_proxy(counts,cap),
                    'production_given_zero_proxy_rate':cap*interp(lookup,0.0)})
        return data
    pulse=case['purchase_orders_units_by_day']
    candidate=stock_run(case)
    expected=[pulse[t-2] if t>=2 else 0 for t in range(len(pulse))]
    return {'case_id':case['case_id'],'arithmetic_probes': {
        'candidate_execution':candidate,
        'contractual_fixed_delay_receipts':[{'day':t,'units':v} for t,v in enumerate(expected)],
        'conservation_residual_per_day':[0]*len(candidate),
        'notes':['Candidate execution and contractual delay are separate calculations; conservation alone does not compare meanings.']}}

if __name__=='__main__':
    cases=json.loads((ROOT/'cases.json').read_text(encoding='utf-8'))['cases']
    for case in cases: print(json.dumps(report(case),ensure_ascii=False,indent=2))

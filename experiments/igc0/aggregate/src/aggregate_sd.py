#!/usr/bin/env python3
"""A separate, deliberately coarse 2-hour stock-flow approximation of IGC-0.

NOT the event generator; NOT fitted to hidden oracle or validated for decisions.
Only reference parameters and OPEN_FULL observed arrival *potential* are inputs.
No numerical projections should be represented as validated until error assessed.
"""
from __future__ import annotations
import hashlib,json,math,datetime
from pathlib import Path
from prepare import canonical,sha,write
POLICIES=('no_delivery','open_full','open_offpeak_capped')

def val(packet,where,key):return packet['operating_reference'][where][key]['value']

def simulate(packet,policy):
    assert policy in POLICIES
    ref=packet['operating_reference']
    kitchen_per_win=val(packet,'reference','kitchen_capacity_per_hour')*2
    dispatch_per_win=val(packet,'reference','dispatch_capacity_reference_per_hour')*2
    cash=val(packet,'initial_conditions','cash_mxn')
    stock=val(packet,'initial_conditions','inventory_meals')
    settle_lag=int(val(packet,'reference','settlement_reference_days'))
    threshold=val(packet,'initial_conditions','supplier_reorder_threshold_meals')
    target=val(packet,'initial_conditions','supplier_reorder_target_meals')
    lead=int(val(packet,'initial_conditions','supplier_nominal_lead_days'))
    price_p=val(packet,'reference','presencial_price_mxn')
    price_d=val(packet,'reference','delivery_price_mxn')*(1-val(packet,'reference','platform_fee_fraction'))
    ingredient_cost=val(packet,'reference','meal_input_cost_mxn')
    pack_cost=val(packet,'reference','delivery_packaging_mxn')
    cost_fixed=val(packet,'initial_conditions','fixed_daily_cost_mxn')
    fee_delivery=val(packet,'initial_conditions','delivery_daily_fee_mxn')
    fee_setup=val(packet,'initial_conditions','delivery_setup_mxn')
    backlog_p=0.0;backlog_d=0.0;ready_d=0.0
    delivery_accepted=0;in_p=0;delivered_d=0;delivered_p=0
    outstanding=[];incoming=[];ledger=[];services=[]
    rows=sorted(packet['pos_by_arrival_cohort'],key=lambda x:(x['day'],('valle_am','pico','valle_pm').index(x['window'])))
    if policy!='no_delivery':cash-=fee_setup
    for day in range(1,15):
        day_rows=[x for x in rows if x['day']==day]
        # Supplier receives previously ordered inventory; settlement is *only* based on due dates.
        arriving=sum(q for due,q in incoming if due==day)
        stock+=arriving;incoming=[(due,q) for due,q in incoming if due>day]
        paid=sum(v for due,v in outstanding if due==day)
        cash+=paid;outstanding=[(due,v) for due,v in outstanding if due>day]
        cash-=cost_fixed+(fee_delivery if policy!='no_delivery' else 0)
        p_today=d_today=0
        for record in day_rows:
            p=record['presencial_attempted'];d=record['delivery_attempted']
            if policy=='no_delivery' or (policy=='open_offpeak_capped' and record['window']=='pico'):
                d=0
            elif policy=='open_offpeak_capped':d=min(d,9)
            in_p+=p;delivery_accepted+=d
            backlog_p+=p;backlog_d+=d
            # Coarse aggregate service: proportional sharing within the window, not individual FIFO.
            cap=min(kitchen_per_win, stock,backlog_p+backlog_d)
            if backlog_p+backlog_d:
                p_c=min(backlog_p,int(round(cap*backlog_p/(backlog_p+backlog_d))))
            else:p_c=0
            d_c=min(backlog_d,cap-p_c)
            # Simulated inventory consumption is exactly production, even if orders are awaiting pickup.
            stock-=p_c+d_c
            backlog_p-=p_c;backlog_d-=d_c
            ready_d+=d_c
            sent=min(dispatch_per_win,ready_d)
            ready_d-=sent
            p_today+=p_c;d_today+=sent
            delivered_p+=p_c;delivered_d+=sent
            cash+=p_c*price_p-d_c*pack_cost
            if sent:outstanding.append((day+max(1,settle_lag),sent*price_d))
            services.append({'day':day,'window':record['window'],'presencial_service_completed':p_c,
                'delivery_service_completed':sent,'kitchen_backlog_end':backlog_p+backlog_d,
                'prepared_waiting_dispatch_end':ready_d,'inventory_end':stock})
        if stock<=threshold:
            ordered=max(0,target-stock)
            if ordered:
                # Assumption: material paid when replenishment is ordered.
                cash-=ordered*ingredient_cost
                incoming.append((day+max(1,lead),ordered))
        ledger.append({'day':day,'cash_end_mxn':round(cash,2),'inventory_end':stock,
                       'receivables_end_mxn':round(sum(v for _,v in outstanding),2),
                       'presencial_service_completed':p_today,'delivery_service_completed':d_today})
    return {'policy':policy,'engine':'IGC0_AGGREGATED_REFERENCE_V0_NOT_CALIBRATED',
        'horizon_days':14,'model_kind':'REFERENCE_SIMULATED_NOT_VIRTUAL_INFERRED',
        'assumptions':['2h time step, proportional kitchen allocation (NOT micro-event FIFO)',
                       'No cancellations modeled: backlogs persist to horizon',
                       'Potential demand fixed to observed open_full POS per window',
                       'Supplier paid on reorder, material delivered after nominal lead; consumed stock is NOT charged twice',
                       'Delivery receivables accrue on dispatch; settlements after integer days',
                       'No stage-specific telemetry or hidden mechanism identification'],
        'trace':{'input_packet_sha256':packet['packet_sha256'],
                 'input_reference_source_id':ref['reference']['kitchen_capacity_per_hour']['source_id'],
                 'initial_conditions_source_id':ref['initial_conditions']['cash_mxn']['source_id']},
        'windows':services,'daily':ledger,'total_service_presencial':delivered_p,
        'total_service_delivery':delivered_d,'pending_presencial_end':backlog_p,
        'pending_delivery_kitchen_end':backlog_d,'pending_delivery_dispatch_end':ready_d,
        'final_inventory':stock,'final_cash':round(cash,2),
        'final_receivables':round(sum(v for _,v in outstanding),2)}

def run_public_models(folder,out):
    summary=[]
    for path in sorted(folder.glob('M*.json')):
        p=json.loads(path.read_text());cases={action:simulate(p,action) for action in POLICIES}
        # Model hash and parameters are explicit to make numerical claims auditable, NOT validated.
        for action,run in cases.items():
            run['sha256']=sha(run)
            write(out/'runs'/p['case_id']/f'{action}.json',run)
        observed=p['observed_decision_indicators']
        modeled=cases['open_full']
        observed_p=p['horizon_totals']['presencial_service_window_completed']
        observed_d=p['horizon_totals']['delivery_service_window_completed']
        errs={'presencial_service_abs_error':abs(modeled['total_service_presencial']-observed_p),
              'delivery_service_abs_error':abs(modeled['total_service_delivery']-observed_d),
              'closing_cash_abs_error_mxn':round(abs(modeled['final_cash']-observed['closing_cash_mxn']),2),
              'closing_inventory_abs_error':abs(modeled['final_inventory']-observed['closing_inventory_meals']),
              'closing_receivables_abs_error_mxn':round(abs(modeled['final_receivables']-observed['closing_receivables_mxn']),2)}
        write(out/'diagnostics'/f'{p["case_id"]}.json',{'case_id':p['case_id'],
             'open_full_fit':errs,'status':'UNVALIDATED_AGGREGATE_REFERENCE',
             'not_an_oracle_comparison':True,
             'warning':'Errors reflect both model aggregation and unknown virtual mechanisms; do NOT adjudicate cause.'})
        summary.append({'case_id':p['case_id'],**errs})
    write(out/'aggregate_fit.json',{'status':'NOT_VALIDATED_FOR_POLICY_CHOICES',
        'fit_against_observed_open_full':summary,'compare_policy_from_unvalidated_engine':False})
    return summary

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--inputs',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True)
    args=a.parse_args();res=run_public_models(args.inputs,args.out)
    print('Uncalibrated reference model completed for 8 cases. Median physical cash error:',sorted(r['closing_cash_abs_error_mxn'] for r in res)[4])

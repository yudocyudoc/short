"""Export eight public observation packets and a SEPARATE sealed oracle.

Usage: python src/generate.py --config holdout/config.json --out .
Never commit holdout/config.json, holdout/oracle.json or holdout/traces/.
"""
from __future__ import annotations
from argparse import ArgumentParser
from dataclasses import asdict,replace
from pathlib import Path
from collections import defaultdict
import hashlib,json,sys
from simulator import Config,simulate,ACTIONS,DAY,DAYS,WINDOWS,demand_tape

PUBLIC_SPEC={
    'horizon_days':DAYS,'windows':[
        {'name':name,'start_local':f'{9+int(start//60):02d}:00',
         'end_local':f'{9+int(end//60):02d}:00','hours':2}
        for name,start,end in WINDOWS],
    'reference':{
        'kitchen_capacity_per_hour':16,'dispatch_capacity_reference_per_hour':15,
        'settlement_reference_days':1,'catering_load_reference_per_day':0,
        'presencial_price_mxn':120,'delivery_price_mxn':130,
        'platform_fee_fraction':0.24,'meal_input_cost_mxn':32,
        'delivery_packaging_mxn':9,'cancellation_after_minutes':205,
        'order_priority':'FIFO por antigüedad de aceptación (cocina compartida)',
        'base_payout_policy':'Delivery liquidado 1 día después en referencia',
        'boundary':'Demanda presencial y delivery, cocina, despacho, inventario, proveedor, cuentas por cobrar, caja',
    },
    'candidate_decisions':{
        'no_delivery':'Sólo presencial',
        'open_full':'Abrir delivery durante tres ventanas',
        'open_offpeak_capped':'Delivery sólo en valle AM/PM, máximo 9 aceptados por ventana',
    },
    'policy_eval':{
        'objective':'Minimizar pérdida operacional definida en protocol.md',
        'service_floor_instore':0.92,'max_delivery_cancel_ratio':0.20,
        'allow_cash_breach_days':0,
        'time_window_type':'Tres ventanas de dos horas; NO promediar el pico como día completo',
        'decision_horizon_days':14,
    },
}
LABELS=('OBSERVADO','CALIBRADO','INFERIDO','SIMULADO','HIPÓTESIS','DESCONOCIDO')

def dump(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def sha(obj):return hashlib.sha256(dump(obj).encode()).hexdigest()
def jwrite(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def source_record(source_id,values,units,kind='OBSERVADO'):
    payload={'source_id':source_id,'values':values,'units':units,'evidence_type':kind}
    return {**payload,'sha256':sha(payload)}

def packet(case_id,cfg,run):
    spec=json.loads(json.dumps(PUBLIC_SPEC))
    # Known starting conditions are fields, not injections.
    spec['initial_conditions']={
        'inventory_meals':cfg.initial_stock,'cash_mxn':cfg.initial_cash,
        'supplier_reorder_threshold_meals':cfg.supplier_threshold,
        'supplier_reorder_target_meals':cfg.supplier_target,
        'supplier_nominal_lead_days':cfg.supplier_lead_days,
        'fixed_daily_cost_mxn':cfg.cash_daily_fixed,
        'delivery_setup_mxn':cfg.delivery_setup,
        'delivery_daily_fee_mxn':cfg.delivery_fee_daily,
    }
    # All reference numbers and initial states have per-field origin/type/unit.
    ref_units={
       'kitchen_capacity_per_hour':'orders/hour',
       'dispatch_capacity_reference_per_hour':'orders/hour',
       'settlement_reference_days':'days',
       'catering_load_reference_per_day':'meals/day',
       'presencial_price_mxn':'MXN/order','delivery_price_mxn':'MXN/order',
       'platform_fee_fraction':'fraction','meal_input_cost_mxn':'MXN/meal',
       'delivery_packaging_mxn':'MXN/order','cancellation_after_minutes':'minutes'
    }
    opening_units={
       'inventory_meals':'meals_equivalent','cash_mxn':'MXN',
       'supplier_reorder_threshold_meals':'meals_equivalent',
       'supplier_reorder_target_meals':'meals_equivalent',
       'supplier_nominal_lead_days':'days','fixed_daily_cost_mxn':'MXN/day',
       'delivery_setup_mxn':'MXN','delivery_daily_fee_mxn':'MXN/day'
    }
    def typed(group,unit_map,kind,source):
        return {k:{'value':v,'unit':unit_map[k], 'evidence_type':kind,
                   'source_id':source,'sha256':sha({'metric':k,'value':v,
                     'unit':unit_map[k],'source_id':source,'evidence_type':kind})}
                if k in unit_map else v for k,v in group.items()}
    spec['reference']=typed(spec['reference'],ref_units,'CALIBRADO','REF:ENGINEERING:v0.1')
    spec['initial_conditions']=typed(spec['initial_conditions'],opening_units,'OBSERVADO','OPENING:REGISTER:v0.1')
    spec['horizon_days']={'value':DAYS,'unit':'days','source_id':'EXPERIMENT:PROTOCOL:v0.1',
                          'evidence_type':'CALIBRADO'}
    spec['horizon_days']['sha256']=sha(spec['horizon_days'])
    for wd in spec['windows']:
        wd['hours']={'value':wd['hours'],'unit':'hours','source_id':'EXPERIMENT:PROTOCOL:v0.1',
                     'evidence_type':'CALIBRADO'}
        wd['hours']['sha256']=sha(wd['hours'])
    spec['policy_eval']['service_floor_instore']={'value':.92,'unit':'fraction',
        'source_id':'EXPERIMENT:PROTOCOL:v0.1','evidence_type':'CALIBRADO'}
    spec['policy_eval']['service_floor_instore']['sha256']=sha(spec['policy_eval']['service_floor_instore'])
    spec['policy_eval']['max_delivery_cancel_ratio']={'value':.20,'unit':'fraction',
        'source_id':'EXPERIMENT:PROTOCOL:v0.1','evidence_type':'CALIBRADO'}
    spec['policy_eval']['max_delivery_cancel_ratio']['sha256']=sha(spec['policy_eval']['max_delivery_cancel_ratio'])
    for k,unit in (('allow_cash_breach_days','days'),('decision_horizon_days','days')):
        spec['policy_eval'][k]={'value':spec['policy_eval'][k],'unit':unit,
           'source_id':'EXPERIMENT:PROTOCOL:v0.1','evidence_type':'CALIBRADO'}
        spec['policy_eval'][k]['sha256']=sha(spec['policy_eval'][k])
    # Do not include scenario type, injected parameter, seed or role.
    windows=[]
    for r in run['rows']:
        units={k:('day_index' if k=='day' else 'label' if k=='window' else 'orders') for k in r}
        windows.append(source_record(f'POS:D{r["day"]:02}:{r["window"]}',r,units))
    daily=[]
    for r in run['daily']:
        u={'day':'day_index','inventory_end':'meals_equivalent',
           'cash_end_mxn':'MXN','receivables_end_mxn':'MXN'}
        daily.append(source_record(f'LEDGER:D{r["day"]:02}',r,u))
    notes=[]
    # Case-specific operational documentation, if present and audited.
    if cfg.catering_daily:
        notes.append(source_record('OPS:EXTERNAL_CONTRACT',{
            'contracted_kitchen_meals_per_day':cfg.catering_daily,
            'schedule':'pico','observed_in_POS':False,
        },{'contracted_kitchen_meals_per_day':'meals/day',
           'schedule':'label','observed_in_POS':'boolean'}))
    elif cfg.gate_role=='couriers' and not cfg.holdout_pair:
        notes.append(source_record('PARTNER:COURIER_AGREEMENT',{
            'delivery_pickup_max_per_hour':cfg.gate_per_hour,
        },{'delivery_pickup_max_per_hour':'orders/hour'}))
    # Two confounded worlds intentionally provide no stage-specific records.
    packet={'case_id':case_id,'schema_version':'IGC-0-observation-v0.1',
            'data_origin':'MUNDO_SINTÉTICO; no observaciones empresariales reales',
            'labels_allowed':LABELS,
            'analysis_task':'Construir grafo SD mínimo; distinguir ideal de virtual; contrastar y proponer acción en 14 días; abstenerse cuando mecanismos no identificables',
            'operating_reference':spec,
            'evidence':{'pos_by_arrival_cohort':windows,
                        'daily_stock_finance_snapshots':daily,
                        'operating_notes':notes},
            'limitations':{
                'event_times_raw_available':False,
                'kitchen_stage_trace_available':False,
                'pickup_stage_trace_available':False,
                'source_row_hashes_prove':'Integridad de fila, NO verdad externa',
                'grouping_pos':'Resultados agrupados por ventana de llegada del pedido, no por hora de completado',
                'service_window_counts':'Completados por ventana real de entrega, separados de cohortes de llegada',
                'requests_attempted':'Demanda potencial registrada en POS/plataforma durante operación virtual con delivery abierto',
            }}
    packet['packet_sha256']=sha(packet)
    return packet

def ideal_from(cfg):
    # Reference matches the initial conditions and potential arrivals;
    # only mechanisms are set to the declared feasible reference.
    return replace(cfg,peak_mult=1,payout_days=1,gate_per_hour=15,
                   gate_role='none',catering_daily=0)

def run_all(config_path,root):
    configs=json.loads(Path(config_path).read_text())
    assert len(configs)==8 and len({x['case_id'] for x in configs})==8
    root=Path(root)
    output=[]
    for entry in configs:
        case=entry['case_id'];cfg=Config(**entry['params'])
        reference=ideal_from(cfg)
        arrivals=demand_tape(cfg)
        world_runs={a:simulate(cfg,a,demand_override=arrivals) for a in ACTIONS}
        ideal_runs={a:simulate(reference,a,demand_override=arrivals) for a in ACTIONS}
        typical_arrivals=demand_tape(reference)
        typical_runs={a:simulate(reference,a,demand_override=typical_arrivals) for a in ACTIONS}
        virtual=world_runs['open_full']
        pub=packet(case,cfg,virtual)
        jwrite(root/'public'/case/'packet.json',pub)
        loss={a:world_runs[a]['metrics'] for a in ACTIONS}
        feasible=[a for a in ACTIONS if loss[a]['viable']]
        decision=min(feasible,key=lambda a:(loss[a]['loss'],a)) if feasible else 'no_feasible_action'
        deltas={a:round(loss[a]['loss']-ideal_runs[a]['metrics']['loss'],2) for a in ACTIONS}
        oracle={'case_id':case,'kind':entry['class'],'injection':entry['injection'],
                'config':asdict(cfg),'reference':asdict(reference),
                'oracle_evidence_type':'SIMULADO',
                'reference_typical_field_metrics':{a:r['metrics'] for a,r in typical_runs.items()},
                'demand_typical_field_sha256':sha(typical_arrivals),
                'observations_sha256':pub['packet_sha256'],
                'world_metrics':loss,
                'ideal_metrics':{a:r['metrics'] for a,r in ideal_runs.items()},
                'loss_delta_virtual_minus_reference':deltas,
                'decision_if_identified':decision,
                'counterfactual_probe':{
                    name:simulate(cfg,'open_full',intervention=name,demand_override=arrivals)['metrics']
                    for name in ('extra_packaging','extra_couriers','extra_kitchen')},
                'world_event_trace_sha256':sha(virtual['internal_events']),
                'demand_tape_sha256':sha(arrivals)}
        jwrite(root/'holdout'/'oracle'/f'{case}.json',oracle)
        # Event-level diagnostic truth never part of the analyst's packet.
        jwrite(root/'holdout'/'event_traces'/f'{case}.json',virtual['internal_events'])
        output.append({'case_id':case,'packet_sha256':pub['packet_sha256'],
                       'oracle_sha256':sha(oracle)})
    jwrite(root/'public'/'index.json', {'experiment':'IGC-0',
         'cases':[{'case_id':r['case_id'],'packet_sha256':r['packet_sha256']} for r in output],
         'contains_ground_truth':False,'case_order_has_no_semantic_meaning':True})
    return output

if __name__=='__main__':
    parser=ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--out',default='.')
    a=parser.parse_args()
    print(json.dumps(run_all(a.config,a.out),indent=2))

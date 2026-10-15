#!/usr/bin/env python3
"""IGC-0 prototype: typed graph scaffold, source-integrity validator, deterministic Mermaid.

All generated scaffold in this module is an ENGINEERING BASELINE, not an LLM result.
Nothing here can use the evaluator's hidden oracle. Do not compute counterfactuals
without a separate calibrated aggregate simulation engine and run provenance.
"""
from __future__ import annotations
import argparse,hashlib,json,re
from pathlib import Path
from prepare import write,sha

ALLOWED={'OBSERVADO','CALIBRADO','INFERIDO','SIMULADO','HIPÓTESIS','DESCONOCIDO'}
DECISIONS={'no_delivery','open_full','open_offpeak_capped','abstain'}


def reference_graph(packet):
    cid=packet['case_id']
    ref=packet['operating_reference']['reference']
    ini=packet['operating_reference']['initial_conditions']
    obs=packet['pos_by_arrival_cohort'][0]
    pos={'source_id':obs['source_id'],'sha256':obs['sha256']}
    def mark(field):
        x=ref[field];return {'source_id':x['source_id'],'sha256':x['sha256']}
    def begin(field):
        x=ini[field];return {'source_id':x['source_id'],'sha256':x['sha256']}
    def stock(id,unit,initial=None,ref=None):
        return {'id':id,'unit':unit,'initial':initial,'initial_label':'OBSERVADO' if initial is not None else 'DESCONOCIDO',
                'initial_refs':[ref] if ref else [],'interpretation':'acumulación persistente'}
    stocks=[stock('orders_waiting_kitchen','orders'),
            stock('delivery_awaiting_dispatch','orders'),
            stock('ingredient_inventory','meals_equivalent',ini['inventory_meals']['value'],begin('inventory_meals')),
            stock('delivery_receivables','MXN',None),
            stock('cash','MXN',ini['cash_mxn']['value'],begin('cash_mxn'))]
    def pipe(id,src,dst,unit,mechanism,refs,rate_source=None):
        return {'id':id,'from':src,'to':dst,'unit_per_time':unit,'mechanism':mechanism,
                'evidence_refs':refs,'capacity_source':rate_source,'epistemic':'INFERIDO'}
    pipes=[
        pipe('admit_instore','instore_external','orders_waiting_kitchen','orders/window','Solicitudes presenciales aceptadas', [pos]),
        pipe('admit_delivery','delivery_external','orders_waiting_kitchen','orders/window','Solicitudes delivery aceptadas', [pos]),
        pipe('kitchen_to_instore','orders_waiting_kitchen','instore_completed','orders/hour', 'Preparación y entrega presencial reguladas por cocina compartida',[mark('kitchen_capacity_per_hour')],mark('kitchen_capacity_per_hour')),
        pipe('kitchen_to_dispatch','orders_waiting_kitchen','delivery_awaiting_dispatch','orders/hour','Preparación delivery ingresa al despacho',[mark('kitchen_capacity_per_hour')],mark('kitchen_capacity_per_hour')),
        pipe('dispatch_delivery','delivery_awaiting_dispatch','delivery_completed','orders/hour','Despacho de pedidos delivery',[mark('dispatch_capacity_reference_per_hour')],mark('dispatch_capacity_reference_per_hour')),
        pipe('inventory_replenish','supplier_external','ingredient_inventory','meals_equivalent/day','Reposición del proveedor',[begin('supplier_nominal_lead_days')]),
        pipe('inventory_consume','ingredient_inventory','consumed_ingredients','meals_equivalent/window','Ingredientes empleados al preparar',[mark('meal_input_cost_mxn')]),
        pipe('delivery_accrual','platform_sales','delivery_receivables','MXN/day','Ingreso neto devengado pendiente de liquidación',[mark('delivery_price_mxn'),mark('platform_fee_fraction')]),
        pipe('platform_settlement','delivery_receivables','cash','MXN/day','Transferencia diferida de plataforma',[mark('settlement_reference_days')]),
        pipe('instore_cash','instore_sales','cash','MXN/day','Cobro presencial',[mark('presencial_price_mxn')]),
        pipe('cash_outgo','cash','external_expenses','MXN/day','Compras y costos operativos',[begin('fixed_daily_cost_mxn')]),
    ]
    return {'case_id':cid,'model_kind':'REFERENCE_GRAPH_SCAFFOLD',
        'is_llm_generated':False,'stocks':stocks,'pipes':pipes,
        'informational_links':[{'from':'ingredient_inventory','to':'kitchen_to_instore','type':'information',
                                'why':'inventario disponible regula servicio'},
                               {'from':'ingredient_inventory','to':'kitchen_to_dispatch','type':'information',
                                'why':'inventario disponible regula servicio'},
                               {'from':'cash','to':'inventory_replenish','type':'information',
                                'why':'liquidez puede restringir reposición, mecanismo hipotético'}],
        'boundary':{'inside':['cocina','colas de servicio','despacho','proveedor','inventario','cuentas por cobrar','caja'],
                    'outside':['demanda del mercado','plataforma','contratos no identificados'],
                    'possible_omissions':['uso de cocina externo','restricción de repartidores','decisiones de clientes']},
        'contrast':[],
        'identifiability':{'status':'insufficient_data',
            'rival_mechanisms':['cuello de botella en cocina compartida','cuello de botella en despacho','choque de demanda'],
            'discriminating_measurement':'Registro individual timestamp de inicio y fin de cocina, retiro por repartidor y cola entre etapas'},
        'actions':['no_delivery','open_full','open_offpeak_capped'],
        'decision':{'choice':'abstain','reason':'No existe aún simulador SD agregado validado para las dos políticas no observadas',
                    'assumptions':['Las observaciones corresponden a open_full','No se infieren contrafactuales desde la misma serie']},
        'scenario_projections':[],
        'unknowns':['Tiempos individuales y procesos ocultos no observados','Parámetros operativos reales de virtual y condiciones contrafactuales']}


def all_evidence_refs(packet):
    e={}
    for r in packet['source_ledger']:
        e[(r['source_id'],r['sha256'])]=r['kind']
    def collect(x):
        if isinstance(x,dict):
            if {'source_id','sha256','evidence_type'}<=x.keys():
                e[(x['source_id'],x['sha256'])]=x['evidence_type']
            for v in x.values():collect(v)
        elif isinstance(x,list):
            for v in x:collect(v)
    collect(packet['operating_reference'])
    return e


def validate_model(model,packet):
    issues=[]
    def issue(code,reason):issues.append({'code':code,'reason':reason})
    if not isinstance(model,dict):return {'accepted':False,'issues':[{'code':'SCHEMA','reason':'Expected object'}]}
    if model.get('case_id')!=packet['case_id']:issue('CASE_ID','Wrong case identifier')
    stocks=model.get('stocks');pipes=model.get('pipes');contrasts=model.get('contrast')
    if not isinstance(stocks,list) or not isinstance(pipes,list) or not isinstance(contrasts,list):
        return {'accepted':False,'issues':[{'code':'SCHEMA','reason':'stocks,pipes,contrast must be lists'}]}
    stockids=[s.get('id') for s in stocks if isinstance(s,dict)]
    pipeids=[p.get('id') for p in pipes if isinstance(p,dict)]
    if len(stockids)!=len(stocks) or not stockids or len(stockids)!=len(set(stockids)):
        issue('STOCK_ID','Missing, invalid or repeated stock ids')
    if len(pipeids)!=len(pipes) or not pipeids or len(pipeids)!=len(set(pipeids)):
        issue('PIPE_ID','Missing, invalid or repeated pipe ids')
    refs=all_evidence_refs(packet)
    def check_refs(items,at):
        if not isinstance(items,list):issue('REFS',f'{at}: evidence references must be list');return
        for r in items:
            if not isinstance(r,dict) or (r.get('source_id'),r.get('sha256')) not in refs:
                issue('UNVERIFIED_SOURCE',f'{at}: unrecognized source_id or sha256')
    for s in stocks:
        if not isinstance(s,dict):continue
        if s.get('initial_label') not in ALLOWED:issue('EPISTEMIC','Stock label missing/invalid')
        check_refs(s.get('initial_refs',[]),s.get('id'))
        if s.get('initial') is not None and not isinstance(s['initial'],(int,float)):
            issue('STOCK_INITIAL','Stock initial amount not numeric')
    for p in pipes:
        if not isinstance(p,dict):continue
        if not all(isinstance(p.get(k),str) and p[k] for k in ('id','from','to','unit_per_time','mechanism')):
            issue('PIPE_SCHEMA','Pipe missing id/from/to/units/mechanism')
        if p.get('epistemic') not in ALLOWED:issue('EPISTEMIC','Pipe label invalid')
        check_refs(p.get('evidence_refs',[]),p.get('id'))
        x=p.get('capacity_source')
        if x is not None:check_refs([x],p.get('id')+':capacity')
    for c in contrasts:
        if not isinstance(c,dict):issue('CONTRAST','Invalid contrast entry');continue
        if c.get('epistemic') not in ALLOWED:issue('EPISTEMIC','Contrast label invalid')
        if c.get('type') not in ('difference','possible_difference','none'):
            issue('CONTRAST','Unknown contrast type')
        check_refs(c.get('evidence_refs',[]),'contrast')
    ident=model.get('identifiability',{})
    if ident.get('status') not in ('identifiable','non_identifiable','no_material_deviation','insufficient_data'):
        issue('IDENTIFIABILITY','Unsupported identifiability status')
    if model.get('decision',{}).get('choice') not in DECISIONS:
        issue('DECISION','Unsupported policy choice')
    for proj in model.get('scenario_projections',[]):
        if not isinstance(proj,dict):issue('PROJECTION','Projection must be object');continue
        for key in ('model_run_id','horizon_days','decision','model_sha256','parameter_sha256','initial_state_sha256'):
            if key not in proj or not proj[key]:issue('PROJECTION_PROVENANCE',f'Missing {key}')
        if proj.get('decision') not in DECISIONS-{'abstain'}:issue('PROJECTION_POLICY','Unsupported policy')
        if not isinstance(proj.get('metrics'),list):issue('PROJECTION','metrics must be list');continue
        for m in proj['metrics']:
            if not isinstance(m,dict) or m.get('label')!='SIMULADO':
                issue('PROJECTED_LABEL','Any numerical projection must be labeled SIMULADO');continue
            for key in ('id','value','unit','source_id','sha256'):
                if key not in m:issue('PROJECTED_TRACE',f'Missing {key}')
    return {'accepted':not issues,'issues':issues,
            'stock_count':len(stocks),'pipe_count':len(pipes),'contrast_count':len(contrasts)}


def diagram(model):
    # Diagram is a pure projection of typed JSON, not separately LLM-written art.
    sid=lambda s:re.sub(r'[^A-Za-z0-9_]','_',str(s))
    stocks={s['id'] for s in model['stocks']}
    lines=['flowchart LR']
    nodes=set()
    for s in model['stocks']:
        text=s['id'].replace('_',' ')
        lines.append(f'    {sid(s["id"])}[("{text}")]')
        nodes.add(s['id'])
    for p in model['pipes']:
        for end in (p['from'],p['to']):
            if end not in nodes:
                txt=end.replace('_',' ')
                lines.append(f'    {sid(end)}["{txt}"]')
                nodes.add(end)
        label=p['id'].replace('_',' ')
        lines.append(f'    {sid(p["from"])} -->|"{label}"| {sid(p["to"])}')
    for l in model.get('informational_links',[]):
        # target is pipe id; Mermaid needs a node to indicate pipe's regulatory link.
        target='control_'+sid(l['to'])
        lines.append(f'    {target}{{"{l["to"].replace("_"," ")}"}}')
        lines.append(f'    {sid(l["from"])} -.-> {target}')
    return '\n'.join(lines)+'\n'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    summary=[]
    for path in sorted(args.inputs.glob('M*.json')):
        p=json.loads(path.read_text())
        graph=reference_graph(p)
        verdict=validate_model(graph,p)
        if not verdict['accepted']:raise RuntimeError(f'{p["case_id"]}: {verdict["issues"]}')
        write(args.out/'models'/path.name,graph)
        (args.out/'diagrams').mkdir(parents=True,exist_ok=True)
        (args.out/'diagrams'/f'{p["case_id"]}.mmd').write_text(diagram(graph))
        write(args.out/'validation'/path.name,verdict)
        summary.append({'case_id':p['case_id'],'model_type':'REFERENCE_GRAPH_SCAFFOLD',
                        'validated_provenance':True,'llm_generated':False,'projection_count':0,
                        'decision':'abstain'})
    write(args.out/'model_manifest.json',{'models':summary,'status':'STRUCTURAL_SCAFFOLD_ONLY',
                                           'simulator_calibrated':False,'llm_inferences':0})
    print(f'{len(summary)} baseline graphs generated, verified and rendered (no LLM, no counterfactual numeric forecasts)')
if __name__=='__main__':main()

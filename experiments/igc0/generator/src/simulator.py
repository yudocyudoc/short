"""IGC-0 synthetic discrete-event generator. No SD integrator used for world truth.

Operations are individual arrivals, service slots, inventory acquisitions and
payment settlement events. Observed data are aggregates of these events.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import heapq, hashlib, json, math, random
from collections import defaultdict, deque

DAY=1440
OPEN=540 # 09:00
WINDOWS=(('valle_am',0,120),('pico',120,240),('valle_pm',240,360))
DAYS=14
ACTIONS=('no_delivery','open_full','open_offpeak_capped')
PRESENTIAL=(9,13,8)
DELIVERY=(6,11,7)

@dataclass(frozen=True)
class Config:
    seed:int
    peak_mult:float=1.0
    payout_days:int=1
    kitchen_per_hour:int=16
    dispatch_per_hour:int=15
    gate_per_hour:int=15
    gate_role:str='none'      # none|packaging|couriers; hidden causal identity
    catering_daily:int=0     # outside POS, occupies kitchen and inventory
    supplier_lead_days:int=1
    supplier_cash_only:bool=True
    supplier_target:int=125
    supplier_threshold:int=47
    initial_stock:int=92
    initial_cash:int=4600
    cash_daily_fixed:int=1650
    demand_scale:float=1.0
    delivery_fee_daily:int=300
    delivery_setup:int=900
    holdout_pair:bool=False

class Evt:
    __slots__=('t','priority','n','kind','payload')
    def __init__(self,t,priority,n,kind,payload):
        self.t,self.priority,self.n,self.kind,self.payload=t,priority,n,kind,payload
    def __lt__(self,other):
        return (self.t,self.priority,self.n)<(other.t,other.priority,other.n)

def _poisson(rng,mu):
    # Knuth works with our modest arrival counts. Entirely deterministic per seed.
    threshold=math.exp(-mu);k=0;p=1.
    while p>threshold:
        k+=1;p*=rng.random()
    return k-1

def demand_tape(cfg:Config):
    """All potential arrivals are independent of action (common random numbers)."""
    arrivals=[];serial=0
    for day in range(DAYS):
        for w,(label,start,end) in enumerate(WINDOWS):
            for channel,baserate in (('presencial',PRESENTIAL[w]),('delivery',DELIVERY[w])):
                # Independent stream per day/window/channel: an injected peak shock
                # cannot change unrelated arrivals by consuming RNG draws.
                rng=random.Random(f'{cfg.seed}|{day}|{label}|{channel}')
                mu=baserate*cfg.demand_scale
                if channel=='delivery' and label=='pico':mu*=cfg.peak_mult
                n=_poisson(rng,mu)
                for i in range(n):
                    minute=day*DAY+OPEN+start+rng.uniform(0,120)
                    serial+=1
                    arrivals.append({'id':f'o{serial:05d}','at':round(minute,3),
                                    'day':day+1,'window':label,'channel':channel})
    return sorted(arrivals,key=lambda a:(a['at'],a['id']))

def _wd(t):
    day=int(t//DAY)
    m=t-day*DAY-OPEN
    if m<0 or m>=360:return (day+1,'fuera_horario')
    return day+1, WINDOWS[min(2,int(m//120))][0]

def simulate(cfg:Config,action='open_full',intervention=None,demand_override=None):
    """Execute a 14-day, event-driven operational world. Policy determines admissions.

    Delivery 'gate' is real in all worlds, but its latent identity matters only
    for counterfactual interventions. POS never sees the identity.
    """
    assert action in ACTIONS
    rng=random.Random(cfg.seed+9901)
    potential=demand_tape(cfg) if demand_override is None else demand_override
    eventq=[];counter=0
    def push(t,priority,kind,payload=None):
        nonlocal counter
        counter+=1;heapq.heappush(eventq,Evt(round(t,4),priority,counter,kind,payload))
    for item in potential:push(item['at'],2,'arrival',item)
    slots={}
    for day in range(DAYS):
        for idx,(name,start,end) in enumerate(WINDOWS):
            t0=day*DAY+OPEN+start
            kitchen_rate=cfg.kitchen_per_hour
            gate_rate=cfg.gate_per_hour
            if intervention=='extra_kitchen':kitchen_rate+=9
            if intervention=='extra_packaging' and cfg.gate_role=='packaging':gate_rate+=15
            if intervention=='extra_couriers' and cfg.gate_role=='couriers':gate_rate+=15
            # 2-hour windows with ordered slots model process/service events.
            for i in range(kitchen_rate*2):
                push(t0+(i+.51)*120/(2*kitchen_rate),3,'kitchen_slot',{'day':day+1,'window':name})
            for i in range(gate_rate*2):
                push(t0+(i+.83)*120/(2*gate_rate),4,'gate_slot',{'day':day+1,'window':name})
        push(day*DAY+OPEN+360,6,'close_day',{'day':day+1})
        if cfg.catering_daily:
            for i in range(cfg.catering_daily):
                # Catering is a separate kitchen workload not registered in POS.
                push(day*DAY+OPEN+120+(i+.5)*120/cfg.catering_daily,2,'catering_arrival',{'day':day+1})
    # State/counters
    qs={ch:deque() for ch in ('presencial','delivery','catering')}
    ready=deque();orders={};accept_in_window=defaultdict(int)
    inv=cfg.initial_stock;cash=float(cfg.initial_cash);ar=0.;costs=0.;margin=0.
    acquisitions=0;material_used=0;cash_breach=0;settled=0.
    earned_net_revenue=0.;packaging_expense=0.
    procurement_pending=False
    status=defaultdict(lambda:defaultdict(int))
    queue_wait=[];events=[]
    total_orders=0
    def log(kind,t,**data):events.append({'event':kind,'t':round(t,3),**data})
    def mark(t,ch,field,n=1):
        day,window=_wd(t)
        status[(day,window)][f'{ch}_{field}']+=n
    def mark_order(order,field,n=1):
        # POS query is grouped by the original order cohort, not event timestamp.
        day,window=_wd(order['arrival'])
        status[(day,window)][f"{order['channel']}_{field}"]+=n
    cutoff=(DAYS-1)*DAY+OPEN+360
    while eventq:
        e=heapq.heappop(eventq);t=e.t;d,w=_wd(t)
        if t>cutoff:break
        if e.kind=='arrival':
            item=e.payload;ch=item['channel'];total_orders+=1
            mark(t,ch,'attempted')
            accept=True
            if ch=='delivery':
                if action=='no_delivery':accept=False
                elif action=='open_offpeak_capped':
                    accept=w!='pico' and accept_in_window[(d,w)]<9
            if not accept:
                mark(t,ch,'declined');log('declined',t,channel=ch,id=item['id']);continue
            accept_in_window[(d,w)]+=1
            order={'id':item['id'],'channel':ch,'arrival':t,'accepted':True,
                   'done':False,'canceled':False,'cooked':False}
            orders[item['id']]=order;qs[ch].append(order)
            mark(t,ch,'accepted');log('accepted',t,channel=ch,id=item['id'])
            push(t+205,5,'expire',order)
        elif e.kind=='catering_arrival':
            item={'id':f'catering-{e.n}','channel':'catering','arrival':t,
                  'accepted':True,'done':False,'canceled':False,'cooked':False}
            qs['catering'].append(item)
            log('outside_POS_catering',t)
        elif e.kind=='kitchen_slot':
            # Shared capacity, FIFO across channels; no special delivery priority.
            choice=None
            for ch in ('presencial','catering','delivery'):
                while qs[ch] and (qs[ch][0]['canceled'] or qs[ch][0]['done']):qs[ch].popleft()
            available=[qs[ch][0] for ch in qs if qs[ch]]
            if available:
                choice=min(available,key=lambda z:z['arrival'])
                qs[choice['channel']].popleft()
            if choice is None:continue
            if inv<=0:
                qs[choice['channel']].appendleft(choice)
                mark(t,choice['channel'],'blocked_stock')
                continue
            inv-=1;material_used+=1
            choice['cooked']=True
            log('kitchen_consumed',t,channel=choice['channel'],id=choice['id'])
            if choice['channel']=='delivery':
                ready.append(choice)
                mark(t,'delivery','cooked')
            elif choice['channel']=='presencial':
                choice['done']=True
                mark_order(choice,'fulfilled')
                mark(t,'presencial','service_window_completed')
                wait=t-choice['arrival'];queue_wait.append(wait)
                cash+=120
                earned_net_revenue+=120
                log('delivered',t,channel='presencial',id=choice['id'],wait_min=round(wait,2))
            else:
                choice['done']=True
                log('outside_POS_catering_completed',t,id=choice['id'])
        elif e.kind=='gate_slot':
            while ready and (ready[0]['canceled'] or ready[0]['done']):ready.popleft()
            if not ready:continue
            order=ready.popleft()
            order['done']=True
            mark_order(order,'fulfilled');mark(t,'delivery','service_window_completed')
            wait=t-order['arrival'];queue_wait.append(wait)
            net=round(130*.76,2)
            ar+=net
            earned_net_revenue+=net
            packaging_expense+=9
            cash-=9
            push(t+cfg.payout_days*DAY,0,'settlement',{'amount':net})
            log('delivered',t,channel='delivery',id=order['id'],wait_min=round(wait,2))
        elif e.kind=='expire':
            order=e.payload
            if not order['done'] and not order['canceled']:
                order['canceled']=True
                mark_order(order,'canceled')
                log('canceled',t,channel=order['channel'],id=order['id'],cooked=order['cooked'])
                if order['cooked']:
                    # Already consumed ingredient; no cash collected.
                    # Spoiled prepared delivery: material consumed; extra handling expense.
                    packaging_expense+=9
                    cash-=9
        elif e.kind=='settlement':
            val=e.payload['amount'];ar-=val;cash+=val;settled+=val
            log('settlement',t,amount=val)
        elif e.kind=='restock':
            units=e.payload['qty'];inv+=units;procurement_pending=False
            acquisitions+=units
            log('restock',t,qty=units)
        elif e.kind=='close_day':
            cash-=cfg.cash_daily_fixed;costs+=cfg.cash_daily_fixed
            if action!='no_delivery':
                extra=cfg.delivery_fee_daily+(cfg.delivery_setup if e.payload['day']==1 else 0)
                cash-=extra;costs+=extra
            if cash<0:cash_breach+=1
            # One pending supplier order at a time, with purchases bound by cash.
            if inv<=cfg.supplier_threshold and not procurement_pending:
                qty=max(0,cfg.supplier_target-inv)
                bill=qty*32
                if not cfg.supplier_cash_only or cash>=bill:
                    cash-=bill;costs+=bill
                    procurement_pending=True
                    supply_day=(e.payload['day']-1)+max(1,cfg.supplier_lead_days)
                    push(supply_day*DAY+OPEN+0.1,0,'restock',{'qty':qty})
                    log('procurement_order',t,qty=qty,paid=bill)
                else:
                    log('supplier_cash_blocked',t,would_buy=qty,cash=round(cash,2))
            log('close_day',t,day=e.payload['day'],inventory=inv,cash=round(cash,2),receivables=round(ar,2))

    # Construct observed series from POS counts (not from hidden source labels).
    rows=[]
    for day in range(1,DAYS+1):
        for name,_,_ in WINDOWS:
            r={'day':day,'window':name}
            for ch in ('presencial','delivery'):
                for field in ('attempted','accepted','declined','canceled','fulfilled','service_window_completed'):
                    r[f'{ch}_{field}']=status[(day,name)].get(f'{ch}_{field}',0)
            rows.append(r)
    # arrivals could be censored from POS if the delivery decision closes; demand
    # tape still identifies potential delivery market in oracle (counterfactual).
    # Summaries at day-end are synthetic observable ledger data.
    daily=[]
    for item in events:
        if item['event']=='close_day':
            daily.append({'day':item['day'],'inventory_end':item['inventory'],
                          'cash_end_mxn':item['cash'],'receivables_end_mxn':item['receivables']})
    end=(DAYS-1)*DAY+OPEN+360
    unfinished=sum(1 for x in orders.values() if not x['done'] and not x['canceled'])
    fulfilled_p=sum(r['presencial_fulfilled'] for r in rows)
    fulfilled_d=sum(r['delivery_fulfilled'] for r in rows)
    cancellations=sum(r['presencial_canceled']+r['delivery_canceled'] for r in rows)
    attempts=sum(r['presencial_attempted']+r['delivery_attempted'] for r in rows)
    declines=sum(r['presencial_declined']+r['delivery_declined'] for r in rows)
    # Predeclare decision loss: economic margin, service cost, liquidity and queues.
    overdue=sum(1 for x in queue_wait if x>65)
    in_store_canceled=sum(r['presencial_canceled'] for r in rows)
    delivery_canceled=sum(r['delivery_canceled'] for r in rows)
    has_delivery=action!='no_delivery'
    delivery_fixed=(cfg.delivery_setup+DAYS*cfg.delivery_fee_daily) if has_delivery else 0
    operating_margin=(earned_net_revenue-32*material_used-packaging_expense-
                      DAYS*cfg.cash_daily_fixed-delivery_fixed)
    loss=round(-operating_margin+220*in_store_canceled+20*delivery_canceled+
               9*overdue+110*cash_breach+3*unfinished,2)
    in_store_attempts=sum(r['presencial_attempted'] for r in rows)
    in_store_service=round(fulfilled_p/in_store_attempts,4) if in_store_attempts else 1.0
    delivery_accepted=sum(r['delivery_accepted'] for r in rows)
    delivery_cancel_rate=round(delivery_canceled/delivery_accepted,4) if delivery_accepted else 0.0
    viable=(in_store_service>=.92 and cash_breach==0 and delivery_cancel_rate<=.20)
    return {'rows':rows,'daily':daily,'internal_events':events,'demand_tape':potential,
            'metrics':{'action':action,'loss':loss,'fulfilled_instore':fulfilled_p,
                       'fulfilled_delivery':fulfilled_d,'cancellations':cancellations,
                       'declined':declines,'attempted':attempts,'cash_end':round(cash,2),
                       'ar_end':round(ar,2),'inventory_end':inv,'stock_used':material_used,
                       'acquisitions':acquisitions,'supplier_cash_breach_days':cash_breach,
                       'unfinished':unfinished,'late_orders':overdue,
                       'operating_margin':round(operating_margin,2),
                       'in_store_service':in_store_service,
                       'delivery_cancel_rate':delivery_cancel_rate,
                       'viable':viable,
                       'kitchen_gate_role':cfg.gate_role}}

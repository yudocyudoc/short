'use strict';

// Local-first prototype: no fetch(), analytics, localStorage, cookies, or AI calls.
const VERSION = '0.1.0';
const sessionStart = new Date().toISOString();
let step = 0;
let selectedView = 'intake';
let observables = [];
let candidates = [];
let assessments = [];
const $ = (id) => document.getElementById(id);
const val = (id) => $(id)?.value?.trim() ?? '';
const splitLines = (str) => str.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
const clean = (value) => value == null ? '' : String(value).trim();
const esc = (value) => clean(value).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
function toast(msg) { const node=$('toast'); node.textContent=msg; node.classList.add('show'); window.clearTimeout(toast.timer); toast.timer=window.setTimeout(()=>node.classList.remove('show'),3100); }
function saveFile(content, filename) {const blob=new Blob([content],{type:'application/json;charset=utf-8'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();window.setTimeout(()=>URL.revokeObjectURL(url),1500);}
const choices = (items, selected) => items.map(([value,label])=>`<option value="${esc(value)}" ${selected===value?'selected':''}>${esc(label)}</option>`).join('');
const statuses=[['observed','Observada'],['proxy','Proxy / aproximación'],['latent','Latente'],['unmeasured','No medida']];
const lanes=[['D','Determinista · moléculas / linter'],['S','SD-AI · propuesta estructural']];
const kinds=[['assessment','Clef · evaluación'],['parameter','Clairic · parámetro'],['deterministic_estimate','Determinismo · parámetro de contraste']];
const captions=[['0','Encuadre'],['1','Observabilidad'],['2','Evidencia y reserva'],['3','Entrada a ARENA']];
const headings=[
 ['01 / CONTRATO DE INVESTIGACIÓN','Antes de explicar, delimitar.','Define la pregunta, quién puede actuar y qué cree que sucede el agente antes de mostrarle cualquier reconstrucción.'],
 ['02 / CONTRATO DE OBSERVABILIDAD','Lo medido no es todo lo real.','Registra qué variables son observadas, cuáles son proxies y cuáles permanecen sin medir. Incluye unidades, resolución y error.'],
 ['03 / PROCEDENCIA Y CONTROL DE ACCESO','Una reserva no es un campo oculto.','La custodia debe separarse antes de la extracción, el índice y los prompts. Aquí registramos referencias, nunca el contenido reservado.'],
 ['04 / CONTRATO DE ENTRADA A ARENA','Confrontar sin fusionar.','Las vías entregan propuestas separadas. ARENA recibe referencias tipadas, comprueba contratos y prepara pruebas discriminantes; no elige al ganador por consenso.']
];
function reRenderRows(){
 $('observables-list').innerHTML=observables.map((o,i)=>`<div class="repeat-row" data-group="observables" data-index="${i}"><div class="repeat-head"><strong>Variable ${String(i+1).padStart(2,'0')}</strong><button type="button" class="remove-row" data-remove="observables" data-index="${i}">Eliminar</button></div><div class="field-grid two"><label class="field">ID de variable<input data-key="id" placeholder="ventas_hora" value="${esc(o.id)}" /></label><label class="field">Estado observable<select data-key="status">${choices(statuses,o.status)}</select></label></div><div class="field-grid two"><label class="field">Unidad<input data-key="unit" placeholder="tickets/h" value="${esc(o.unit)}" /></label><label class="field">Resolución temporal<input data-key="resolution" placeholder="15 min / día" value="${esc(o.resolution)}" /></label></div><div class="field-grid two"><label class="field">Error / incertidumbre<input data-key="measurement_error" placeholder="desconocido / ±3" value="${esc(o.measurement_error)}" /></label><label class="field">Retraso de conocimiento<input data-key="reporting_lag" placeholder="24 h" value="${esc(o.reporting_lag)}" /></label></div><label class="field">Fuente de medición o procedencia<input data-key="source_ref" placeholder="src-tickets" value="${esc(o.source_ref)}" /></label></div>`).join('') || '<p class="card-note">Todavía no hay variables registradas.</p>';
 $('candidates-list').innerHTML=candidates.map((c,i)=>`<div class="repeat-row" data-group="candidates" data-index="${i}"><div class="repeat-head"><strong>Candidato ${String(i+1).padStart(2,'0')}</strong><button type="button" class="remove-row" data-remove="candidates" data-index="${i}">Eliminar</button></div><div class="field-grid two"><label class="field">ID candidato<input data-key="id" placeholder="mecanismo-a" value="${esc(c.id)}" /></label><label class="field">Vía de origen<select data-key="lane">${choices(lanes,c.lane)}</select></label></div><label class="field">Referencia a propuesta / IR tipado<input data-key="proposal_ref" placeholder="ir:CAF-001:A@v1" value="${esc(c.proposal_ref)}" /></label><label class="field">Referencia a parámetros (opcional)<input data-key="parameter_set_ref" placeholder="params:A@v1" value="${esc(c.parameter_set_ref)}" /></label></div>`).join('') || '<p class="card-note">Los candidatos llegarán después de que las vías terminen su primera ronda ciega. Puedes dejar esta sección vacía.</p>';
 $('assessments-list').innerHTML=assessments.map((a,i)=>`<div class="repeat-row" data-group="assessments" data-index="${i}"><div class="repeat-head"><strong>Propuesta evaluativa ${String(i+1).padStart(2,'0')}</strong><button type="button" class="remove-row" data-remove="assessments" data-index="${i}">Eliminar</button></div><div class="field-grid two"><label class="field">ID de propuesta<input data-key="id" placeholder="eval-tasa-servicio" value="${esc(a.id)}" /></label><label class="field">Tipo<select data-key="kind">${choices(kinds,a.kind)}</select></label></div><div class="field-grid two"><label class="field">Pregunta o parámetro objetivo<input data-key="target_ref" placeholder="service_rate" value="${esc(a.target_ref)}" /></label><label class="field">Referencia de salida<input data-key="result_ref" placeholder="claims:run-02:q1" value="${esc(a.result_ref)}" /></label></div><label class="field">Procedencia / versión de modelo<input data-key="provenance_ref" placeholder="clef:run-02@sha / clairic:run-04" value="${esc(a.provenance_ref)}" /></label></div>`).join('') || '<p class="card-note">La salida de Clef o Clairic no es obligatoria para abrir una investigación. Si todavía no existe, queda pendiente.</p>';
}
function blankObservable(){return {id:'',status:'observed',unit:'',resolution:'',measurement_error:'UNKNOWN',reporting_lag:'',source_ref:''};}
function blankCandidate(){return {id:'',lane:'D',proposal_ref:'',parameter_set_ref:''};}
function blankAssessment(){return {id:'',kind:'assessment',target_ref:'',result_ref:'',provenance_ref:''};}
function readIntake(){
 return {
  schema_version:'igc.investigation_intake.v0.1',case_id:val('caseId'),status:'DRAFT',
  inquiry:{system_name:val('systemName'),problem_statement:val('problem'),research_question:val('researchQuestion'),actor:val('actor'),researcher_role:val('researcherRole'),declared_purpose:val('declaredPurpose'),perceived_field:{description:val('perceivedField'),captured_before_reconstruction:val('perceivedField')!==''?'DECLARED_BY_OPERATOR_NOT_VERIFIED':'PENDING'},system_boundary:val('boundary'),horizon_date:val('horizon'),intervention_authorization:val('permission')},
  observability:observables.filter(o=>o.id.trim()).map(o=>({...o})),
  evidence:{as_known_at:val('cutoff') ? new Date(val('cutoff')).toISOString() : null,visible_source_refs:splitLines(val('sourceRefs')),extraction_mode:val('extractionMode'),confidentiality:val('privacyNotes'),holdout:{reference:val('holdoutRef')||null,custodian:val('holdoutCustodian')||null,test_type:val('holdoutType'),contents_included:false,server_isolation_verified:false}},
  provenance:{created_at:sessionStart,authoring_mode:'BROWSER_ONLY_NO_STORAGE',version:VERSION}
 };
}
function readArena(){
 const intake=readIntake();
 const chosen=splitLines(val('arenaObservables'));
 return {
  schema_version:'igc.arena_input.v0.1',status:'DRAFT_PENDING_EXTERNAL_GATES',case_id:intake.case_id,
  snapshot:{as_known_at:intake.evidence.as_known_at,allowed_source_refs:intake.evidence.visible_source_refs,holdout_ref:intake.evidence.holdout.reference,holdout_custodian:intake.evidence.holdout.custodian,holdout_contents_exposed:false,isolation_assurance:'UNVERIFIED_LOCAL_PROTOTYPE'},
  round:{id:val('roundId')||'R1',rival_outputs_hidden_until_round_closed:true,simulation_budget:Math.max(1,Math.min(1000,Number(val('simulationBudget'))||12)),baseline_ref:val('baselineRef')||null},
  observability:intake.observability,
  structure_proposals:candidates.filter(c=>c.id.trim()).map(c=>({candidate_id:c.id,lane:c.lane,proposal_ref:c.proposal_ref,parameter_set_ref:c.parameter_set_ref||null,validation:{g1:'NOT_RUN',g2:'NOT_RUN',g3:'NOT_RUN'}})),
  assessment_parameter_proposals:assessments.filter(a=>a.id.trim()).map(a=>({proposal_id:a.id,kind:a.kind,target_ref:a.target_ref,result_ref:a.result_ref,provenance_ref:a.provenance_ref})),
  evaluation_plan:{target_observable_ids:chosen,allowed_perturbations:splitLines(val('allowedPerturbations')),horizon_date:intake.inquiry.horizon_date,prediction_lock_required:$('requirePredictionLock').checked,holdout_access:'EVALUATOR_ONLY',comparison_mode:'PER_CANDIDATE_NO_VOTE'},
  intervention_authorization:intake.inquiry.intervention_authorization,
  invariant_guards:{no_gold_in_input:true,holdout_never_sent_to_builders:true,competitors_not_merged:true,modelica_result_not_truth:true},
  provenance:{created_at:sessionStart,authoring_mode:'BROWSER_ONLY_NO_STORAGE',version:VERSION}
 };
}
function checks(){
 const a=readIntake(),b=readArena(),allids=a.observability.map(o=>o.id),ids=new Set(allids);
 const base=[
  {ok:!!a.case_id && !!a.inquiry.system_name,text:'ID y sistema identificados'},
  {ok:!!a.inquiry.research_question && !!a.inquiry.horizon_date,text:'Pregunta y horizonte definidos'},
  {ok:a.observability.length>0 && a.observability.every(x=>x.unit && x.status),text:'Variables con estado y unidades'},
  {ok:ids.size===allids.length,text:'IDs de variables sin duplicados'},
  {ok:!!a.evidence.as_known_at,text:'Corte temporal as-known-at registrado'},
  {ok:!!a.evidence.holdout.reference && !!a.evidence.holdout.custodian,text:'Custodio y referencia de reserva identificados'}
 ];
 const arena=[
  ...base,
  {ok:b.structure_proposals.length>=2 && b.structure_proposals.every(x=>x.proposal_ref),text:'Al menos dos candidatos estructurales referenciados'},
  {ok:b.evaluation_plan.target_observable_ids.length>0 && b.evaluation_plan.target_observable_ids.every(id=>ids.has(id)),text:'Observables de contraste existen en la ficha'},
  {ok:b.evaluation_plan.prediction_lock_required,text:'Congelamiento previo a la reserva requerido'},
  {ok:false,text:'G1, G2, G3 y custodia real: deben verificarse externamente'}
 ];
 return {intake:base,arena};
}
function updateNav(){const a=readIntake(),c=checks();const stepOk=[c.intake[0].ok && c.intake[1].ok,c.intake[2].ok && c.intake[3].ok,c.intake[4].ok && c.intake[5].ok,c.arena[6].ok && c.arena[7].ok];document.querySelectorAll('.nav-step').forEach((n,i)=>{n.classList.toggle('current',i===step);n.setAttribute('aria-current',i===step?'step':'false');const indicator=n.querySelector('.nav-status');indicator.textContent=stepOk[i]?'✓':'○';});}
function refreshPreview(){
 const data=selectedView==='intake'?readIntake():readArena();const text=JSON.stringify(data,null,2);
 $('json-preview').textContent=text; $('json-lines').textContent=`${text.split('\n').length} líneas`;
 const items=checks()[selectedView];$('validation-list').replaceChildren();for(const item of items){const row=document.createElement('div');row.className='check-row';const icon=document.createElement('span');icon.className=item.ok?'check':'pending';icon.textContent=item.ok?'✓':'○';const label=document.createElement('span');label.textContent=item.text;row.append(icon,label);$('validation-list').append(row);}
 const complete=items.every(x=>x.ok);$('inspector-state').textContent=complete?'COMPLETO · NO VALIDADO':'BORRADOR';$('inspector-state').classList.toggle('good',complete);
 updateNav();
}
function navigate(i){step=Math.max(0,Math.min(3,i));document.querySelectorAll('.stage').forEach((s,k)=>s.classList.toggle('active',k===step));const [eyebrow,title,intro]=headings[step];$('step-eyebrow').textContent=eyebrow;$('step-title').textContent=title;$('step-intro').textContent=intro;$('stage-count').textContent=`Paso ${step+1} de 4`;$('prev-step').disabled=step===0;$('next-step').textContent=step===3?'Volver a encuadre ↺':'Siguiente →';updateNav();window.scrollTo({top:0,behavior:'smooth'});}
function readDemo(){
 const demo={caseId:'CAF-DEMO-001',systemName:'Cafetería ficticia — piloto',problem:'El propietario quiere comprender por qué las ventas parecen estables pese a que percibe mayor afluencia.',actor:'Propietario',researchQuestion:'¿Las ventas están limitadas por demanda o por capacidad de atención?',researcherRole:'observer',boundary:'Llegadas, colas, capacidad de atención y ventas. Competencia externa solo como hipótesis.',declaredPurpose:'Aumentar ventas sin deteriorar la experiencia',perceivedField:'La dirección sospecha que el producto atrae visitas, pero no se ha verificado la explicación.',horizon:'2026-12-01',permission:'observe_only',cutoff:'2026-10-21T12:00',extractionMode:'human',sourceRefs:'src-demo-entrevista-r1\nsrc-demo-tickets-sep',privacyNotes:'Ficción metodológica: no se han agregado datos reales.',holdoutRef:'HOLD-DEMO-001',holdoutCustodian:'Evaluador externo (ficticio)',holdoutType:'future_observation',roundId:'R1',simulationBudget:'12',baselineRef:'baseline:demanda-vs-capacidad-demo',arenaObservables:'ventas_hora\ncola_minutos',allowedPerturbations:'Simular cambio en capacidad. Sin intervención real.'};
 Object.entries(demo).forEach(([id,v])=>{if($(id))$(id).value=v;});$('requirePredictionLock').checked=true;
 observables=[{id:'ventas_hora',status:'observed',unit:'tickets/h',resolution:'1 h',measurement_error:'UNKNOWN',reporting_lag:'24 h',source_ref:'src-demo-tickets-sep'},{id:'cola_minutos',status:'unmeasured',unit:'min',resolution:'UNKNOWN',measurement_error:'UNKNOWN',reporting_lag:'UNKNOWN',source_ref:''}];
 candidates=[{id:'M-DEMO-A',lane:'D',proposal_ref:'draft:estructura-a',parameter_set_ref:''},{id:'M-DEMO-B',lane:'S',proposal_ref:'draft:estructura-b',parameter_set_ref:''}];
 assessments=[{id:'P-DEMO-01',kind:'parameter',target_ref:'service_rate',result_ref:'draft:parameter-proposal',provenance_ref:'DEMO-NO_INFERENCE'}];
 reRenderRows();refreshPreview();toast('Demo ficticia cargada; no es un resultado de investigación.');
}
function applyIntake(obj){if(obj?.schema_version!=='igc.investigation_intake.v0.1')throw Error('Por ahora solo se importa el contrato de investigación v0.1');const q=obj.inquiry||{},e=obj.evidence||{},h=e.holdout||{};
 const map={caseId:obj.case_id,systemName:q.system_name,problem:q.problem_statement,actor:q.actor,researchQuestion:q.research_question,researcherRole:q.researcher_role,boundary:q.system_boundary,declaredPurpose:q.declared_purpose,perceivedField:q.perceived_field?.description,horizon:q.horizon_date,permission:q.intervention_authorization,cutoff:e.as_known_at?e.as_known_at.slice(0,16):'',extractionMode:e.extraction_mode,sourceRefs:(e.visible_source_refs||[]).join('\n'),privacyNotes:e.confidentiality,holdoutRef:h.reference,holdoutCustodian:h.custodian,holdoutType:h.test_type};
 for(const [id,v] of Object.entries(map)){if($(id) && v!=null){$(id).value=String(v)}}
 observables=(Array.isArray(obj.observability)?obj.observability:[]).slice(0,100).map(x=>({id:clean(x.id),status:statuses.some(([v])=>v===x.status)?x.status:'unmeasured',unit:clean(x.unit),resolution:clean(x.resolution),measurement_error:clean(x.measurement_error),reporting_lag:clean(x.reporting_lag),source_ref:clean(x.source_ref)}));
 candidates=[];assessments=[];reRenderRows();refreshPreview();navigate(0);
}
document.querySelectorAll('[data-step]').forEach(btn=>btn.addEventListener('click',()=>navigate(Number(btn.dataset.step))));
$('next-step').addEventListener('click',()=>navigate(step===3?0:step+1));$('prev-step').addEventListener('click',()=>navigate(step-1));
$('add-observable').addEventListener('click',()=>{observables.push(blankObservable());reRenderRows();refreshPreview()});
$('add-candidate').addEventListener('click',()=>{candidates.push(blankCandidate());reRenderRows();refreshPreview()});
$('add-assessment').addEventListener('click',()=>{assessments.push(blankAssessment());reRenderRows();refreshPreview()});
const repeaterMap={observables:()=>observables,candidates:()=>candidates,assessments:()=>assessments};
document.addEventListener('click',(e)=>{const btn=e.target.closest('[data-remove]');if(!btn)return;const group=btn.dataset.remove;const rows=repeaterMap[group]?.();if(!rows)return;rows.splice(Number(btn.dataset.index),1);reRenderRows();refreshPreview();});
document.addEventListener('input',(e)=>{const el=e.target,wrap=el.closest('.repeat-row');if(wrap && el.dataset.key){const rows=repeaterMap[wrap.dataset.group]?.();if(rows?.[Number(wrap.dataset.index)])rows[Number(wrap.dataset.index)][el.dataset.key]=el.value;}refreshPreview();});
document.addEventListener('change',(e)=>{const el=e.target,wrap=el.closest('.repeat-row');if(wrap && el.dataset.key){const rows=repeaterMap[wrap.dataset.group]?.();if(rows?.[Number(wrap.dataset.index)])rows[Number(wrap.dataset.index)][el.dataset.key]=el.value;}refreshPreview();});
$('show-intake').addEventListener('click',()=>{selectedView='intake';$('show-intake').classList.add('selected');$('show-arena').classList.remove('selected');refreshPreview()});
$('show-arena').addEventListener('click',()=>{selectedView='arena';$('show-arena').classList.add('selected');$('show-intake').classList.remove('selected');refreshPreview()});
$('copy-json').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(JSON.stringify(selectedView==='intake'?readIntake():readArena(),null,2));toast('Contrato copiado al portapapeles.');}catch{toast('No se pudo copiar: usa Exportar contrato.');}});
$('download-json').addEventListener('click',()=>{const contract=selectedView==='intake'?readIntake():readArena();const prefix=selectedView==='intake'?'investigacion':'arena';saveFile(JSON.stringify(contract,null,2)+'\n',`${prefix}-${contract.case_id||'borrador'}-v0.1.json`);toast('Borrador descargado. Requiere validación externa.');});
$('import-button').addEventListener('click',()=>$('import-file').click());
$('import-file').addEventListener('change',async(e)=>{const file=e.target.files[0];if(!file)return;try{if(file.size>1500000)throw Error('El archivo supera el límite de 1.5 MB');const obj=JSON.parse(await file.text());applyIntake(obj);toast('Ficha importada correctamente.');}catch(err){toast(`No se pudo importar: ${err.message}`);}finally{e.target.value='';}});
$('demo-button').addEventListener('click',readDemo);
reRenderRows();navigate(0);refreshPreview();


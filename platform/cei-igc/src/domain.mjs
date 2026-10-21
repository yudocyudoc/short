export const VERSION = 'igc.cloud_workbench.v0.2';
export const casePattern = /^[A-Za-z0-9][A-Za-z0-9_-]{1,63}$/;
const statuses = new Set(['observed','proxy','latent','unmeasured']);
const guards = ['gold','holdout_data','holdout_contents','reserved_payload','hidden_world_contents','future_observation_data','evaluation_answer'];

export class InputError extends Error { constructor(message, code=400) { super(message); this.status=code; } }
export function assert(condition,message,code=400){ if(!condition) throw new InputError(message,code); }
export function encode(data) { return new TextEncoder().encode(typeof data==='string'?data:JSON.stringify(data)); }
export async function sha256(data) {
  const digest=await crypto.subtle.digest('SHA-256',encode(data));
  return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
function onlyKeys(obj,allowed,label){assert(plain(obj),`Objeto requerido: ${label}`);assert(Object.keys(obj).every(k=>allowed.includes(k)),`Campos inesperados en ${label}`);}
function plain(value){return value!==null && typeof value==='object' && !Array.isArray(value);}
function scanForbiddenKeys(obj,depth=0){
  assert(depth<16,'Documento excesivamente anidado');
  if(!obj || typeof obj!=='object')return;
  for(const [key,val] of Object.entries(obj)) {
    assert(!guards.includes(key.toLowerCase()),`No está permitido enviar el campo reservado ${key}`);
    scanForbiddenKeys(val,depth+1);
  }
}
export function validateDraft(intake,arena=null){
  assert(plain(intake),'Se requiere contrato de investigación');
  assert(intake.schema_version==='igc.investigation_intake.v0.1','Contrato de investigación no compatible');
  assert(intake.status==='DRAFT','Solo se aceptan borradores');
  onlyKeys(intake,['schema_version','case_id','status','inquiry','observability','evidence','provenance'],'investigación');
  assert(typeof intake.case_id==='string' && casePattern.test(intake.case_id),'ID de caso inválido: usa letras, números, guion o guion bajo');
  assert(plain(intake.inquiry) && plain(intake.evidence),'Faltan encuadre o evidencia');
  onlyKeys(intake.inquiry,['system_name','problem_statement','research_question','actor','researcher_role','declared_purpose','perceived_field','system_boundary','horizon_date','intervention_authorization'],'encuadre');
  onlyKeys(intake.inquiry.perceived_field,['description','captured_before_reconstruction'],'campo percibido');
  onlyKeys(intake.evidence,['as_known_at','visible_source_refs','extraction_mode','confidentiality','holdout'],'evidencia');
  onlyKeys(intake.provenance,['created_at','authoring_mode','version'],'procedencia');
  assert(plain(intake.provenance) && intake.provenance.authoring_mode==='BROWSER_ONLY_NO_STORAGE','Procedencia de autoría incompatible');
  const h=intake.evidence.holdout;
  assert(plain(h) && h.contents_included===false && h.server_isolation_verified===false,'Solo se acepta referencia de reserva, nunca contenidos');
  assert(Object.keys(h).every(k=>['reference','custodian','test_type','contents_included','server_isolation_verified'].includes(k)),'Campos de reserva no permitidos');
  assert(Array.isArray(intake.evidence.visible_source_refs) && intake.evidence.visible_source_refs.length<=500,'Referencias de evidencia inválidas');
  assert(Array.isArray(intake.observability) && intake.observability.length<=100,'Observabilidad inválida');
  for(const v of intake.observability){
    assert(plain(v) && typeof v.id==='string' && statuses.has(v.status),'Variable observable inválida');
    onlyKeys(v,['id','status','unit','resolution','measurement_error','reporting_lag','source_ref'],'variable');
  }
  scanForbiddenKeys(intake);
  if(arena!==null){
    assert(plain(arena) && arena.schema_version==='igc.arena_input.v0.1','Contrato ARENA incompatible');
    assert(arena.case_id===intake.case_id,'ARENA pertenece a otro caso');
    assert(arena.status==='DRAFT_PENDING_EXTERNAL_GATES','ARENA solo puede estar en borrador');
    onlyKeys(arena,['schema_version','status','case_id','snapshot','round','observability','structure_proposals','assessment_parameter_proposals','evaluation_plan','intervention_authorization','invariant_guards','provenance'],'ARENA');
    onlyKeys(arena.snapshot,['as_known_at','allowed_source_refs','holdout_ref','holdout_custodian','holdout_contents_exposed','isolation_assurance'],'snapshot');
    onlyKeys(arena.round,['id','rival_outputs_hidden_until_round_closed','simulation_budget','baseline_ref'],'ronda');
    onlyKeys(arena.evaluation_plan,['target_observable_ids','allowed_perturbations','horizon_date','prediction_lock_required','holdout_access','comparison_mode'],'plan');
    onlyKeys(arena.invariant_guards,['no_gold_in_input','holdout_never_sent_to_builders','competitors_not_merged','modelica_result_not_truth'],'invariantes');
    onlyKeys(arena.provenance,['created_at','authoring_mode','version'],'procedencia ARENA');
    for(const c of arena.structure_proposals){
      onlyKeys(c,['candidate_id','lane','proposal_ref','parameter_set_ref','validation'],'candidato');
      onlyKeys(c.validation,['g1','g2','g3'],'gates');
    }
    for(const q of arena.assessment_parameter_proposals)onlyKeys(q,['proposal_id','kind','target_ref','result_ref','provenance_ref'],'evaluación');
    assert(arena.snapshot?.holdout_contents_exposed===false && arena.snapshot?.isolation_assurance==='UNVERIFIED_LOCAL_PROTOTYPE', 'ARENA no puede declarar custodia verificada');
    assert(Array.isArray(arena.structure_proposals) && arena.structure_proposals.every(c=>c.validation?.g1==='NOT_RUN'&&c.validation?.g2==='NOT_RUN'&&c.validation?.g3==='NOT_RUN'),'La interfaz no puede aprobar las compuertas G1–G3');
    assert(arena.invariant_guards?.no_gold_in_input===true && arena.invariant_guards?.holdout_never_sent_to_builders===true && arena.invariant_guards?.competitors_not_merged===true && arena.invariant_guards?.modelica_result_not_truth===true,'Invariantes de aislamiento ausentes');
    assert(arena.evaluation_plan?.holdout_access==='EVALUATOR_ONLY' && arena.evaluation_plan?.comparison_mode==='PER_CANDIDATE_NO_VOTE','Plan de arena no permitido');
    assert(arena.round?.rival_outputs_hidden_until_round_closed===true,'Ronda sin ceguera declarada');
    scanForbiddenKeys(arena);
  }
  const bytes=encode({intake,arena}).length;
  assert(bytes<=240000,'Contrato demasiado grande');
  return {intake,arena};
}
export function validatePreflightReady(intake){
  validateDraft(intake);
  assert(Boolean(intake.inquiry.system_name?.trim() && intake.inquiry.research_question?.trim() && intake.inquiry.horizon_date?.trim()),'Completa sistema, pregunta y horizonte antes de solicitar la sonda');
  assert(Boolean(intake.evidence.as_known_at),'Define el corte temporal antes de solicitar la sonda');
  assert(intake.observability.length>0,'Registra al menos una variable observable');
}
export function publicCase(row){ return {case_id:row.case_id,version:row.version,created_at:row.created_at,updated_at:row.updated_at,intake:JSON.parse(row.intake_json),arena:JSON.parse(row.arena_json)}; }
export function publicRun(row){return {job_id:row.job_id,case_id:row.case_id,case_version:row.case_version,status:row.status,github_url:row.github_url,github_run_id:row.github_run_id,snapshot_sha256:row.snapshot_sha256,created_at:row.created_at,updated_at:row.updated_at,error:row.error,result_available:!!row.result_key};}


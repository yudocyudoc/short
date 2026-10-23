/* IGC v0.2: Cloudflare backend companion. No third-party telemetry. */
(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  let savedCaseId = null;
  let serverVersion = null;
  let currentJobId = null;
  function note(text){byId('cloud-status').textContent=text;}
  function jobNote(text){byId('job-status').textContent=text;}
  async function call(url, options={}){
    const res=await fetch(url,{credentials:'same-origin',cache:'no-store',...options,headers:{'Accept':'application/json',...options.headers}});
    let value;try{value=await res.json();}catch{value={error:`HTTP ${res.status}`};}
    if(!res.ok)throw new Error(value.error||`HTTP ${res.status}`);
    return value;
  }
  const payload = obj => ({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
  async function listCases(){
    const list=await call('/api/cases');
    const select=byId('saved-cases');
    select.replaceChildren(new Option('— Selecciona un caso —',''));
    for(const item of list.items||[])select.add(new Option(`${item.case_id} · v${item.version}`,item.case_id));
    if(savedCaseId)select.value=savedCaseId;
    return list;
  }
  async function save(){
    try {
      const intake=readIntake(),arena=readArena(), id=intake.case_id;
      if(!id)throw new Error('Primero registra un ID de caso');
      if(savedCaseId && savedCaseId!==id)throw new Error('El ID cambió: vuelve a cargar o crea otro caso');
      const obj={intake,arena};
      let result;
      if(savedCaseId&&serverVersion!==null)result=await call('/api/cases/'+encodeURIComponent(id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({...obj,expected_version:serverVersion})});
      else result=await call('/api/cases',payload(obj));
      savedCaseId=id;serverVersion=result.version;
      note(`Guardado: ${id} · v${serverVersion}. Solo borrador; ni ARENA ni la reserva están validadas.`);
      await listCases();
    } catch(e){note('No se guardó: '+e.message);}
  }
  async function load(){
    const id=byId('saved-cases').value;
    if(!id){note('Selecciona primero un caso');return;}
    try {
      const value=await call('/api/cases/'+encodeURIComponent(id));
      applyIntake(value.intake);
      if(value.arena){
        candidates=(value.arena.structure_proposals||[]).map(x=>({id:x.candidate_id,lane:x.lane,proposal_ref:x.proposal_ref,parameter_set_ref:x.parameter_set_ref||''}));
        assessments=(value.arena.assessment_parameter_proposals||[]).map(x=>({id:x.proposal_id,kind:x.kind,target_ref:x.target_ref,result_ref:x.result_ref,provenance_ref:x.provenance_ref}));
        const r=value.arena.round||{},p=value.arena.evaluation_plan||{};
        byId('roundId').value=r.id||'R1';byId('simulationBudget').value=r.simulation_budget||12;
        byId('baselineRef').value=r.baseline_ref||'';
        byId('arenaObservables').value=(p.target_observable_ids||[]).join('\n');
        byId('allowedPerturbations').value=(p.allowed_perturbations||[]).join('\n');
        byId('requirePredictionLock').checked=p.prediction_lock_required!==false;
        reRenderRows();refreshPreview();
      }
      savedCaseId=id;serverVersion=value.version;currentJobId=null;
      note(`Cargado ${id}, versión ${serverVersion}. Puedes editar y guardar una versión nueva.`);
      jobNote('Selecciona un trabajo para iniciar una sonda de integración.');
    }catch(e){note('No se pudo cargar: '+e.message);}
  }
  async function launch(){
    try{
      if(!savedCaseId)throw new Error('Primero guarda o carga la investigación');
      const current=readIntake();
      if(current.case_id!==savedCaseId)throw new Error('ID en pantalla distinto del guardado');
      // Only probe existing server snapshot. No inline payload, no arbitrary workflow or model choice.
      const value=await call('/api/cases/'+encodeURIComponent(savedCaseId)+'/runs',payload({kind:'DETERMINISTIC_PROBE'}));
      currentJobId=value.job_id;
      jobNote(`Trabajo ${currentJobId}\nEstado: ${value.status}. Solo sonda de contratos, SIN inferencia ni Modelica.\n${value.github_url||''}`);
    }catch(e){jobNote('No se inició: '+e.message);}
  }
  async function check(){
    if(!currentJobId){
      try{
        if(!savedCaseId)throw new Error('Selecciona un caso guardado');
        const value=await call('/api/cases/'+encodeURIComponent(savedCaseId)+'/runs');
        currentJobId=value.runs?.[0]?.job_id;
      }catch(e){jobNote('No se pudo consultar: '+e.message);return;}
    }
    if(!currentJobId){jobNote('Este caso no tiene ejecuciones');return;}
    try{
      const result=await call('/api/runs/'+encodeURIComponent(currentJobId)+'?refresh=github');
      let text=`Trabajo ${result.job_id}\nEstado: ${result.status}\n${result.github_url||''}`;
      if(result.error)text+='\n'+result.error;
      if(result.result_available){
        const details=await call('/api/runs/'+encodeURIComponent(currentJobId)+'/result');
        text+=`\nSonda determinista: ${details.status}; variables: ${details.observable_count}; IA: ${details.inference_calls}; Modelica: ${details.modelica_executed?'sí':'no'}`;
      }
      jobNote(text);
    }catch(e){jobNote('No se pudo consultar: '+e.message);}
  }
  byId('save-cloud').addEventListener('click',save);
  byId('reload-cloud').addEventListener('click',async()=>{try{await listCases();note('Lista actualizada');}catch(e){note('Lista no disponible: '+e.message);}});
  byId('load-cloud').addEventListener('click',load);
  byId('run-github').addEventListener('click',launch);
  byId('check-job').addEventListener('click',check);
  (async()=>{try{await call('/api/me');await listCases();note('Cloudflare autenticado. Puedes guardar borradores privados.');}catch(e){note('Backend no disponible o sin acceso: '+e.message+'\nEl formulario aún permite exportar JSON localmente.');}})();
})();


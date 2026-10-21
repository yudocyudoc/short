import {InputError,assert,sha256,validateDraft,validatePreflightReady,publicCase,publicRun,casePattern} from './domain.mjs';
import {verifyRunnerRequest} from './security.mjs';

function json(value,status=200){return new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});}
async function readBody(req,max=250000){
 const t=await req.text();
 assert(new TextEncoder().encode(t).length<=max,'Solicitud demasiado grande',413);
 try{return JSON.parse(t);}catch{throw new InputError('JSON inválido');}
}
function fail(error){const status=error instanceof InputError?error.status:500;return json({error:status===500?'Error de servidor':error.message},status);}
const now=()=>new Date().toISOString();
async function findCase(db,id,sub){return db.prepare('SELECT * FROM investigations WHERE case_id=? AND owner_sub=?').bind(id,sub).first();}
async function findJob(db,id){return db.prepare('SELECT * FROM arena_jobs WHERE job_id=?').bind(id).first();}
function validateKey(id){assert(casePattern.test(id),'ID de caso inválido');}
function githubConfig(env){
  const repo=env.GITHUB_REPO||'';
  const workflow=env.GITHUB_WORKFLOW||'';
  const ref=env.GITHUB_REF||'';
  assert(/^[a-zA-Z0-9._-]+\/[a-zA-Z0-9._-]+$/.test(repo),'Repo GitHub no configurado',503);
  assert(/^igc-arena-probe\.ya?ml$/.test(workflow),'Workflow de GitHub no permitido',503);
  assert(ref==='main','Ref GitHub no permitido',503);
  assert(env.GITHUB_TOKEN?.length>10,'Secreto GITHUB_TOKEN no configurado',503);
  return {repo,workflow,ref};
}
async function githubDispatch(env,job,requestFn){
  const {repo,workflow,ref}=githubConfig(env);
  const url=`https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`;
  const response=await requestFn(url,{method:'POST',headers:{'Accept':'application/vnd.github+json','Authorization':'Bearer '+env.GITHUB_TOKEN,'X-GitHub-Api-Version':'2026-03-10','User-Agent':'IGC-Arena-Worker','Content-Type':'application/json'},body:JSON.stringify({ref,return_run_details:true,inputs:{job_id:job.job_id,snapshot_sha256:job.snapshot_sha256}})});
  if(!response.ok)throw new InputError(`GitHub dispatch HTTP ${response.status}`,502);
  let meta={};
  if(response.status!==204){try{meta=await response.json();}catch{ /* older GitHub response supported */ }}
  const github_run_id=meta.workflow_run_id||meta.run_id||meta.id||null;
  const github_url=meta.run_url||meta.html_url||(github_run_id?`https://github.com/${repo}/actions/runs/${github_run_id}`:null);
  return {github_run_id,github_url};
}
async function refreshGithubStatus(env,db,job,requestFn){
  if(!job.github_run_id || ['COMPLETE','ERROR','DISPATCH_ERROR'].includes(job.status))return job;
  const {repo}=githubConfig(env);
  const response=await requestFn(`https://api.github.com/repos/${repo}/actions/runs/${job.github_run_id}`,{headers:{'Accept':'application/vnd.github+json','Authorization':'Bearer '+env.GITHUB_TOKEN,'User-Agent':'IGC-Arena-Worker'}});
  if(!response.ok)return job;
  const meta=await response.json();
  const next=meta.status==='completed'?(meta.conclusion==='success'?'COMPLETE':'ERROR'):meta.status==='in_progress'?'RUNNING':'QUEUED';
  // A successful GitHub workflow without a signed result is NOT a successful IGC probe.
  const effective=next==='COMPLETE' && !job.result_key?'ERROR':next;
  const error=effective==='ERROR'&&!job.result_key?`GitHub terminó (${meta.conclusion||'sin resultado'}), sin callback de resultado verificado`:null;
  await db.prepare('UPDATE arena_jobs SET status=?,error=?,updated_at=? WHERE job_id=? AND status NOT IN (\'COMPLETE\',\'ERROR\',\'DISPATCH_ERROR\')').bind(effective,error,now(),job.job_id).run();
  return await findJob(db,job.job_id);
}

export function createApi({authorize,requestFn=fetch}={}){
  if(typeof authorize!=='function')throw new Error('Secure Access authorizer required');
  return async function api(req,env){
    const url=new URL(req.url),path=url.pathname,method=req.method.toUpperCase();
    try{
      if(path==='/api/health'&&method==='GET')return json({service:'cei-igc-workbench',version:'0.2.0',safe_mode:'DRAFTS_AND_DETERMINISTIC_PROBE_ONLY',authorization:'Cloudflare Access JWT',storage:'D1 + R2'});
      if(path.startsWith('/api/runner/')){
        // Authenticating machine-to-machine requests without an Access user token.
        const m=path.match(/^\/api\/runner\/jobs\/([0-9a-f-]{36})\/(snapshot|result)$/);
        assert(m,'Runner path inválido',404);
        const payload=method==='POST'?await req.text():'';
        await verifyRunnerRequest(req,env,payload);
        const job=await findJob(env.IGC_DB,m[1]);assert(job,'Trabajo desconocido',404);
        if(m[2]==='snapshot'&&method==='GET'){
          const source=await env.IGC_ARTIFACTS.get(job.snapshot_key);
          assert(source,'Snapshot no encontrado',404);
          return new Response(source.body,{headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-IGC-Snapshot-Sha256':job.snapshot_sha256}});
        }
        if(m[2]==='result'&&method==='POST'){
          assert(payload.length<=100000,'Resultado demasiado grande',413);
          let result;try{result=JSON.parse(payload);}catch{throw new InputError('Resultado no es JSON');}
          assert(result.schema_version==='igc.arena_probe.v0.2','Contrato de resultado inválido');
          assert(result.job_id===job.job_id&&result.snapshot_sha256===job.snapshot_sha256,'Resultado no corresponde a snapshot');
          assert(['PASS','FAIL'].includes(result.status)&&result.modelica_executed===false&&result.inference_calls===0,'El probe no puede declarar simulaciones ni IA');
          assert(result.probe_only===true && Number.isInteger(result.observable_count) && result.observable_count>=0 && result.observable_count<=100,'Contrato de sonda inválido');
          assert(Array.isArray(result.issues)&&result.issues.length<=100&&result.issues.every(x=>typeof x==='string'&&x.length<=300),'Lista de incidencias inválida');
          assert(Object.keys(result).every(k=>['schema_version','job_id','snapshot_sha256','status','modelica_executed','inference_calls','gates','probe_only','observable_count','issues'].includes(k)),'Resultado contiene campos no admitidos');
          assert(result.gates?.g1==='NOT_RUN'&&result.gates?.g2==='NOT_RUN'&&result.gates?.g3==='NOT_RUN','El probe no aprueba gates');
          assert(!['COMPLETE','ERROR','DISPATCH_ERROR'].includes(job.status),'Trabajo ya finalizado',409);
          const key=`jobs/${job.job_id}/result.json`;
          await env.IGC_ARTIFACTS.put(key,payload,{httpMetadata:{contentType:'application/json'}});
          await env.IGC_DB.prepare('UPDATE arena_jobs SET status=?,result_key=?,updated_at=? WHERE job_id=?').bind(result.status==='PASS'?'COMPLETE':'ERROR',key,now(),job.job_id).run();
          return json({accepted:true,status:result.status});
        }
        throw new InputError('Método runner no permitido',405);
      }
      const user=await authorize(req,env);
      if(path==='/api/me'&&method==='GET')return json({authenticated:true,subject:user.sub,email:user.email||null});
      assert(env.IGC_DB&&env.IGC_ARTIFACTS,'Faltan bindings D1 o R2',503);
      if(path==='/api/cases'&&method==='GET'){
        const r=await env.IGC_DB.prepare('SELECT case_id,version,updated_at,created_at FROM investigations WHERE owner_sub=? ORDER BY updated_at DESC LIMIT 100').bind(user.sub).all();
        return json({items:r.results||[]});
      }
      if(path==='/api/cases'&&method==='POST'){
        const data=await readBody(req);const {intake,arena}=validateDraft(data.intake,data.arena??null);
        const id=intake.case_id,t=now();
        const found=await findCase(env.IGC_DB,id,user.sub);
        assert(!found,'Ya existe este caso: cárgalo para actualizar',409);
        try{
          await env.IGC_DB.prepare('INSERT INTO investigations (case_id,owner_sub,intake_json,arena_json,version,created_at,updated_at) VALUES (?,?,?,?,1,?,?)')
             .bind(id,user.sub,JSON.stringify(intake),JSON.stringify(arena),t,t).run();
        }catch{throw new InputError('No pudo crearse el caso; comprueba si el ID ya existe',409);}
        return json({case_id:id,version:1,created_at:t,updated_at:t},201);
      }
      const cas=path.match(/^\/api\/cases\/([A-Za-z0-9_-]{2,64})(?:\/(runs))?$/);
      if(cas){
        const id=cas[1];validateKey(id);
        const rec=await findCase(env.IGC_DB,id,user.sub);assert(rec,'Caso inexistente o sin acceso',404);
        if(!cas[2]){
          if(method==='GET')return json(publicCase(rec));
          if(method==='PUT'){
            const data=await readBody(req);
            assert(Number.isInteger(data.expected_version)&&data.expected_version>0,'Se requiere versión esperada');
            const {intake,arena}=validateDraft(data.intake,data.arena??null);
            assert(intake.case_id===id,'No se puede cambiar el ID del caso');
            const t=now();
            const changed=await env.IGC_DB.prepare('UPDATE investigations SET intake_json=?,arena_json=?,version=version+1,updated_at=? WHERE case_id=? AND owner_sub=? AND version=?')
            .bind(JSON.stringify(intake),JSON.stringify(arena),t,id,user.sub,data.expected_version).run();
            assert(changed.meta?.changes===1,'Versión desactualizada: vuelve a cargar el caso',409);
            return json({case_id:id,version:data.expected_version+1,updated_at:t});
          }
        } else if(cas[2]==='runs'){
          if(method==='GET'){
            const runs=await env.IGC_DB.prepare('SELECT * FROM arena_jobs WHERE case_id=? AND owner_sub=? ORDER BY created_at DESC LIMIT 30').bind(id,user.sub).all();
            return json({runs:(runs.results||[]).map(publicRun)});
          }
          if(method==='POST'){
            const data=await readBody(req,10000);
            assert(data.kind==='DETERMINISTIC_PROBE','Solo está habilitada la sonda determinista; nada de modelos IA ni simulaciones');
            validatePreflightReady(JSON.parse(rec.intake_json));
            assert(env.IGC_RUNNER_HMAC_SECRET?.length>=24,'HMAC del runner no configurado',503);
            githubConfig(env);
            const job_id=crypto.randomUUID();const t=now();
            const snapshot={schema_version:'igc.runner_snapshot.v0.2',job_id,case_id:id,case_version:rec.version,intake:JSON.parse(rec.intake_json),arena:JSON.parse(rec.arena_json),data_class:'VISIBLE_METADATA_ONLY',holdout_contents_included:false,modelica_executed:false};
            const raw=JSON.stringify(snapshot),snapshot_sha256=await sha256(raw),snapshot_key=`jobs/${job_id}/snapshot.json`;
            await env.IGC_ARTIFACTS.put(snapshot_key,raw,{httpMetadata:{contentType:'application/json'}});
            await env.IGC_DB.prepare('INSERT INTO arena_jobs (job_id,case_id,owner_sub,snapshot_key,snapshot_sha256,case_version,status,created_at,updated_at) VALUES (?,?,?,?,?,?,\'DISPATCHING\',?,?)')
                  .bind(job_id,id,user.sub,snapshot_key,snapshot_sha256,rec.version,t,t).run();
            let next;
            try{next=await githubDispatch(env,{job_id,snapshot_sha256},requestFn);}
            catch(err){
              await env.IGC_DB.prepare('UPDATE arena_jobs SET status=\'DISPATCH_ERROR\',error=?,updated_at=? WHERE job_id=?').bind(String(err.message).slice(0,240),now(),job_id).run();
              return json({job_id,status:'DISPATCH_ERROR',error:'GitHub no aceptó el workflow; revisa la configuración en el servidor'},502);
            }
            await env.IGC_DB.prepare('UPDATE arena_jobs SET status=\'QUEUED\',github_run_id=?,github_url=?,updated_at=? WHERE job_id=?')
                .bind(next.github_run_id,next.github_url,now(),job_id).run();
            return json({job_id,status:'QUEUED',github_url:next.github_url,snapshot_sha256},202);
          }
        }
      }
      const run=path.match(/^\/api\/runs\/([0-9a-f-]{36})(?:\/(result))?$/);
      if(run&&method==='GET'){
        let job=await findJob(env.IGC_DB,run[1]);
        assert(job&&job.owner_sub===user.sub,'Trabajo inexistente o sin acceso',404);
        if(run[2]){
          assert(job.result_key,'No existe un resultado verificado',404);
          const object=await env.IGC_ARTIFACTS.get(job.result_key);
          assert(object,'Artefacto de resultado inexistente',404);
          return new Response(object.body,{headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
        }
        if(url.searchParams.get('refresh')==='github'){
          try{job=await refreshGithubStatus(env,env.IGC_DB,job,requestFn);}catch{ /* Polling is auxiliary; signed callback remains authoritative */ }
        }
        return json(publicRun(job));
      }
      throw new InputError('Ruta no encontrada',404);
    }catch(error){return fail(error);}
  };
}


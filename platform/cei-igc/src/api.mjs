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
function githubHttpError(status,operation){
  const diagnosis={
    401:'GITHUB_TOKEN invÃ¡lido, caducado o rechazado por GitHub',
    403:'GitHub autenticÃ³ la solicitud, pero denegÃ³ el permiso o aplicÃ³ una restricciÃ³n/rate limit',
    404:'Endpoint no encontrado o recurso, repositorio o workflow no visible para este token',
    422:'GitHub rechazÃ³ la solicitud por validaciÃ³n; revisa workflow_dispatch, ref e inputs',
  }[status]||`respuesta HTTP ${status}`;
  return new InputError(`GitHub ${operation} HTTP ${status}: ${diagnosis}`,502);
}
const githubHeaders=token=>({'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,'X-GitHub-Api-Version':'2026-03-10','User-Agent':'IGC-Arena-Worker'});
async function githubDispatch(env,job,requestFn){
  const {repo,workflow,ref}=githubConfig(env);
  const url=`https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`;
  const response=await requestFn(url,{method:'POST',headers:{...githubHeaders(env.GITHUB_TOKEN),'Content-Type':'application/json'},body:JSON.stringify({ref,inputs:{job_id:job.job_id,snapshot_sha256:job.snapshot_sha256}})});
  if(!response.ok)throw githubHttpError(response.status,'dispatch');
  let meta={};
  if(response.status!==204){try{meta=await response.json();}catch{ /* older GitHub response supported */ }}
  const github_run_id=meta.workflow_run_id||meta.run_id||meta.id||null;
  const github_url=meta.run_url||meta.html_url||(github_run_id?`https://github.com/${repo}/actions/runs/${github_run_id}`:null);
  return {github_run_id,github_url};
}
async function checkGithubAuth(env,requestFn){
  const {repo,workflow}=githubConfig(env);
  // Repository metadata works with fine-grained PATs and GitHub App installation tokens.
  // A repository 404 may also mean missing visibility, not necessarily nonexistence.
  const auth=await requestFn(`https://api.github.com/repos/${repo}`,{method:'GET',headers:githubHeaders(env.GITHUB_TOKEN)});
  if(!auth.ok)throw githubHttpError(auth.status,'repository access check');
  // Confirm read access to the configured workflow; this does not test Actions:write.
  const target=await requestFn(`https://api.github.com/repos/${repo}/actions/workflows/${workflow}`,{method:'GET',headers:githubHeaders(env.GITHUB_TOKEN)});
  if(!target.ok)throw githubHttpError(target.status,'workflow access check');
  return {authenticated:true,workflow_accessible:true};
}
const githubRunId=value=>{
  const id=Number(value);
  return Number.isSafeInteger(id)&&id>0?id:null;
};
async function refreshGithubStatus(env,db,job,requestFn){
  const runId=githubRunId(job.github_run_id);
  if(!runId || ['COMPLETE','ERROR','DISPATCH_ERROR'].includes(job.status))return job;
  const {repo}=githubConfig(env);
  const response=await requestFn(`https://api.github.com/repos/${repo}/actions/runs/${runId}`,{headers:githubHeaders(env.GITHUB_TOKEN)});
  if(!response.ok)return job;
  const meta=await response.json();
  if(githubRunId(meta.id)!==runId || meta.path!==`.github/workflows/${env.GITHUB_WORKFLOW}` || meta.event!=='workflow_dispatch' || meta.head_branch!==env.GITHUB_REF)return job;
  if(meta.status==='completed'&&!job.result_key){
    try{
      const imported=await importGithubArtifact(env,job,requestFn);
      if(imported)return await findJob(db,job.job_id);
    }catch{
      await db.prepare('UPDATE arena_jobs SET status=?,error=?,updated_at=? WHERE job_id=? AND result_key IS NULL AND status NOT IN (\'COMPLETE\',\'ERROR\',\'DISPATCH_ERROR\')')
        .bind('ERROR','Could not verify GitHub result artifact',now(),job.job_id).run();
      return await findJob(db,job.job_id);
    }
  }
  const next=meta.status==='completed'?(meta.conclusion==='success'?'COMPLETE':'ERROR'):meta.status==='in_progress'?'RUNNING':'QUEUED';
  // A successful GitHub workflow without a signed result is NOT a successful IGC probe.
  const effective=next==='COMPLETE' && !job.result_key?'ERROR':next;
  const error=effective==='ERROR'&&!job.result_key?`GitHub completed (${meta.conclusion||'without result'}), no signed result artifact available`:null;
  await db.prepare('UPDATE arena_jobs SET status=?,error=?,updated_at=? WHERE job_id=? AND status NOT IN (\'COMPLETE\',\'ERROR\',\'DISPATCH_ERROR\')').bind(effective,error,now(),job.job_id).run();
  return await findJob(db,job.job_id);
}


const artifactName=job=>`igc-probe-${job.job_id}`;
function safeArtifactDownloadUrl(value){
  let url;try{url=new URL(value);}catch{return false;}
  return url.protocol==='https:'&&!url.username&&!url.password&&(
    url.hostname==='github.com'||url.hostname.endsWith('.githubusercontent.com')||url.hostname.endsWith('.blob.core.windows.net')
  );
}
async function extractArtifactJson(buffer,filename){
  const bytes=new Uint8Array(buffer),view=new DataView(buffer);
  const min=Math.max(0,bytes.length-65557);let eocd=-1;
  for(let i=bytes.length-22;i>=min;i--)if(view.getUint32(i,true)===0x06054b50){eocd=i;break;}
  assert(eocd>=0,'Invalid GitHub artifact ZIP',502);
  const entries=view.getUint16(eocd+10,true),directory=view.getUint32(eocd+16,true);
  let offset=directory;
  for(let i=0;i<entries;i++){
    assert(view.getUint32(offset,true)===0x02014b50,'Invalid artifact ZIP directory',502);
    const method=view.getUint16(offset+10,true),compressed=view.getUint32(offset+20,true),uncompressed=view.getUint32(offset+24,true);
    const nameLength=view.getUint16(offset+28,true),extraLength=view.getUint16(offset+30,true),commentLength=view.getUint16(offset+32,true),local=view.getUint32(offset+42,true);
    const name=new TextDecoder().decode(bytes.subarray(offset+46,offset+46+nameLength));
    if(name===filename||name.endsWith('/'+filename)){
      assert(uncompressed<=100000,'Artifact result is too large',413);
      assert(view.getUint32(local,true)===0x04034b50,'Invalid ZIP entry',502);
      const localName=view.getUint16(local+26,true),localExtra=view.getUint16(local+28,true),start=local+30+localName+localExtra;
      let raw=bytes.slice(start,start+compressed);
      if(method===8){
        try{raw=await readLimited(new Blob([raw]).stream().pipeThrough(new DecompressionStream('deflate-raw')),100000);}
        catch{throw new InputError('Could not decompress GitHub artifact',502);}
      }else assert(method===0,'Unsupported ZIP compression',502);
      assert(raw.length===uncompressed,'ZIP entry size mismatch',502);
      return new TextDecoder('utf-8',{fatal:true}).decode(raw);
    }
    offset+=46+nameLength+extraLength+commentLength;
  }
  throw new InputError('Artifact does not contain the expected result',502);
}
async function readLimited(stream,max){
  assert(stream,'Empty artifact response',502);
  const reader=stream.getReader(),chunks=[];let size=0;
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;assert(size<=max,'Artifact exceeds size limit',413);chunks.push(value);}
  const output=new Uint8Array(size);let offset=0;for(const chunk of chunks){output.set(chunk,offset);offset+=chunk.length;}return output;
}
async function verifyArtifactSignature(secret,job,manifest){
  assert(typeof secret==='string'&&secret.length>=24,'Runner HMAC is not configured',503);
  assert(manifest&&manifest.schema_version==='igc.arena_probe_artifact.v1'&&typeof manifest.result_json==='string','Invalid result manifest',502);
  const digest=await sha256(manifest.result_json);
  assert(manifest.result_sha256===digest,'Artifact result hash mismatch',502);
  const message=`IGC-ARENA-ARTIFACT-V1\\n${job.job_id}\\n${job.snapshot_sha256}\\n${digest}`;
  const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['verify']);
  const signature=manifest.signature||'';
  assert(/^v1=[a-f0-9]{64}$/.test(signature),'Invalid artifact HMAC signature',502);
  const sig=new Uint8Array(signature.slice(3).match(/../g).map(x=>parseInt(x,16)));
  assert(await crypto.subtle.verify('HMAC',key,sig,new TextEncoder().encode(message)),'Invalid artifact HMAC signature',502);
  const result=JSON.parse(manifest.result_json);
  validateProbeResult(result,job);
  return {result,raw:manifest.result_json};
}
function validateProbeResult(result,job){
  assert(result.schema_version==='igc.arena_probe.v0.2','Invalid result contract');
  assert(result.job_id===job.job_id&&result.snapshot_sha256===job.snapshot_sha256,'Result does not match snapshot');
  assert(['PASS','FAIL'].includes(result.status)&&result.modelica_executed===false&&result.inference_calls===0,'Probe cannot declare simulations or AI');
  assert(result.probe_only===true&&Number.isInteger(result.observable_count)&&result.observable_count>=0&&result.observable_count<=100,'Invalid probe result');
  assert(Array.isArray(result.issues)&&result.issues.length<=100&&result.issues.every(x=>typeof x==='string'&&x.length<=300),'Invalid issue list');
  assert(Object.keys(result).every(k=>['schema_version','job_id','snapshot_sha256','status','modelica_executed','inference_calls','gates','probe_only','observable_count','issues'].includes(k)),'Result contains unsupported fields');
  assert(result.gates?.g1==='NOT_RUN'&&result.gates?.g2==='NOT_RUN'&&result.gates?.g3==='NOT_RUN','Probe cannot pass gates');
}
async function importGithubArtifact(env,job,requestFn){
  const runId=githubRunId(job.github_run_id);
  assert(runId,'Invalid GitHub workflow run ID',502);
  const {repo}=githubConfig(env),headers=githubHeaders(env.GITHUB_TOKEN);
  const list=await requestFn(`https://api.github.com/repos/${repo}/actions/runs/${runId}/artifacts`,{headers});
  if(!list.ok)return false;
  const data=await list.json(),artifact=(data.artifacts||[]).find(x=>x.name===artifactName(job)&&!x.expired&&githubRunId(x.workflow_run?.id)===runId);
  if(!artifact)return false;
  assert(Number.isInteger(artifact.size_in_bytes)&&artifact.size_in_bytes>0&&artifact.size_in_bytes<=1000000,'Unexpected artifact size',413);
  const archive=await requestFn(`https://api.github.com/repos/${repo}/actions/artifacts/${artifact.id}/zip`,{headers,redirect:'manual'});
  const location=archive.headers.get('Location');
  if(archive.status!==302||!safeArtifactDownloadUrl(location))throw new InputError('GitHub artifact redirect is not allowed',502);
  // Do not forward GitHub Authorization to the temporary archive URL.
  const downloaded=await requestFn(location,{redirect:'manual'});
  assert(downloaded.ok,'Could not download GitHub artifact',502);
  const zip=await readLimited(downloaded.body,1000000);
  const json=await extractArtifactJson(zip.buffer,'igc-arena-probe-artifact.json');
  const verified=await verifyArtifactSignature(env.IGC_RUNNER_HMAC_SECRET,job,JSON.parse(json));
  const key=`jobs/${job.job_id}/result.json`;
  await env.IGC_ARTIFACTS.put(key,verified.raw,{httpMetadata:{contentType:'application/json'}});
  const status=verified.result.status==='PASS'?'COMPLETE':'ERROR';
  const error=status==='ERROR'?verified.result.issues.join('; ').slice(0,500)||'Deterministic probe reported FAIL':null;
  await env.IGC_DB.prepare('UPDATE arena_jobs SET status=?,result_key=?,error=?,updated_at=? WHERE job_id=? AND result_key IS NULL AND status NOT IN (\'COMPLETE\',\'ERROR\',\'DISPATCH_ERROR\')').bind(status,key,error,now(),job.job_id).run();
  return true;
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
      if(path==='/api/github/auth-check'&&method==='GET')return json(await checkGithubAuth(env,requestFn));
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
            await env.IGC_DB.prepare("UPDATE arena_jobs SET status=CASE WHEN status='DISPATCHING' THEN 'QUEUED' ELSE status END,github_run_id=?,github_url=?,updated_at=? WHERE job_id=?")
                .bind(next.github_run_id,next.github_url,now(),job_id).run();
            const dispatched=await findJob(env.IGC_DB,job_id);
            return json({job_id,status:dispatched.status,github_url:dispatched.github_url,snapshot_sha256},202);
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


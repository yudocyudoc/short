import {InputError,assert} from '../../cei-igc/src/domain.mjs';
import {verifyRunnerRequest} from '../../cei-igc/src/security.mjs';

const json=(value,status=200)=>new Response(JSON.stringify(value),{
  status,
  headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'},
});
const now=()=>new Date().toISOString();
const resultFields=['schema_version','job_id','snapshot_sha256','status','modelica_executed','inference_calls','gates','probe_only','observable_count','issues'];

async function findJob(db,id){
  return db.prepare('SELECT * FROM arena_jobs WHERE job_id=?').bind(id).first();
}

function validateResult(result,job){
  assert(result&&typeof result==='object'&&!Array.isArray(result),'Resultado inválido');
  assert(result.schema_version==='igc.arena_probe.v0.2','Contrato de resultado inválido');
  assert(result.job_id===job.job_id&&result.snapshot_sha256===job.snapshot_sha256,'Resultado no corresponde al snapshot');
  assert(['PASS','FAIL'].includes(result.status)&&result.modelica_executed===false&&result.inference_calls===0,'El runner no puede declarar simulaciones ni IA');
  assert(result.probe_only===true&&Number.isInteger(result.observable_count)&&result.observable_count>=0&&result.observable_count<=100,'Contrato de sonda inválido');
  assert(Array.isArray(result.issues)&&result.issues.length<=100&&result.issues.every(issue=>typeof issue==='string'&&issue.length<=300),'Lista de incidencias inválida');
  assert(Object.keys(result).every(key=>resultFields.includes(key)),'Resultado contiene campos no admitidos');
  assert(result.gates?.g1==='NOT_RUN'&&result.gates?.g2==='NOT_RUN'&&result.gates?.g3==='NOT_RUN','El runner no puede aprobar gates');
}

function fail(error){
  const status=error instanceof InputError?error.status:500;
  return json({error:status===500?'Error interno del runner':error.message},status);
}

export function createRunnerApi(){
  return async function runner(request,env){
    try{
      const {pathname}=new URL(request.url);
      const match=pathname.match(/^\/api\/runner\/jobs\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/(snapshot|result)$/i);
      assert(match,'Ruta no encontrada',404);
      const [,jobId,action]=match;
      const allowedMethod=action==='snapshot'?'GET':'POST';
      assert(request.method===allowedMethod,'Método no permitido',405);
      const body=action==='result'?await request.text():'';
      assert(new TextEncoder().encode(body).byteLength<=100000,'Resultado demasiado grande',413);

      // HMAC authenticates the exact method, URL path, timestamp, and body.
      await verifyRunnerRequest(request,env,body);
      assert(env.IGC_DB&&env.IGC_ARTIFACTS,'Bindings del runner no configurados',503);
      const job=await findJob(env.IGC_DB,jobId);
      assert(job,'Trabajo desconocido',404);

      if(action==='snapshot'){
        assert(['DISPATCHING','QUEUED','RUNNING'].includes(job.status),'Snapshot de trabajo finalizado',409);
        const snapshot=await env.IGC_ARTIFACTS.get(job.snapshot_key);
        assert(snapshot,'Snapshot no encontrado',404);
        return new Response(snapshot.body,{headers:{
          'Content-Type':'application/json',
          'Cache-Control':'no-store',
          'X-IGC-Snapshot-Sha256':job.snapshot_sha256,
          'X-Content-Type-Options':'nosniff',
        }});
      }

      assert(!job.result_key&&!['COMPLETE','ERROR','DISPATCH_ERROR'].includes(job.status),'Callback duplicado o trabajo finalizado',409);
      let result;
      try{result=JSON.parse(body);}catch{throw new InputError('Resultado no es JSON');}
      validateResult(result,job);

      const key=`jobs/${job.job_id}/result.json`;
      let stored;
      try{
        stored=await env.IGC_ARTIFACTS.put(key,body,{
          onlyIf:new Headers({'If-None-Match':'*'}),
          httpMetadata:{contentType:'application/json'},
        });
      }catch(error){
        if(/precondition|412/i.test(String(error)))throw new InputError('Callback duplicado',409);
        throw error;
      }
      assert(stored,'Callback duplicado',409);

      const status=result.status==='PASS'?'COMPLETE':'ERROR';
      const error=status==='ERROR'?result.issues.join('; ').slice(0,500)||'Sonda determinista reportó FAIL':null;
      const updated=await env.IGC_DB.prepare("UPDATE arena_jobs SET status=?,result_key=?,error=?,updated_at=? WHERE job_id=? AND result_key IS NULL AND status IN ('DISPATCHING','QUEUED','RUNNING')")
        .bind(status,key,error,now(),job.job_id).run();
      assert(updated.meta?.changes===1,'Callback duplicado o trabajo finalizado',409);
      return json({accepted:true,status:result.status});
    }catch(error){return fail(error);}
  };
}

const runner=createRunnerApi();
export default {fetch:runner};

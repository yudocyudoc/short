import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createRunnerApi} from '../../cei-igc-runner-v02/src/index.mjs';
import {signRunnerRequest} from '../src/security.mjs';
import {sha256} from '../src/domain.mjs';

const secret='NOT_REAL_TEST_SECRET_32CHARS_LONG_2026';
const jobId='9c8d9e2a-e615-4f57-afa2-3eba5519c9b0';
const snapshot=JSON.stringify({schema_version:'igc.runner_snapshot.v0.2',job_id:jobId,case_id:'CAF-DEMO-001',marker:'PRIVATE_SNAPSHOT_MARKER'});
const snapshotHash=await sha256(snapshot);

class RunnerDB {
  constructor(job){this.job=structuredClone(job);}
  prepare(sql){
    const db=this;let values=[];
    return {
      bind(...args){values=args;return this;},
      async first(){assert.match(sql,/FROM arena_jobs/);return db.job?structuredClone(db.job):null;},
      async run(){
        assert.match(sql,/UPDATE arena_jobs/);
        const [status,resultKey,error,updatedAt,id]=values;
        if(!db.job||db.job.job_id!==id||db.job.result_key||!['DISPATCHING','QUEUED','RUNNING'].includes(db.job.status))return {meta:{changes:0}};
        Object.assign(db.job,{status,result_key:resultKey,error,updated_at:updatedAt});
        return {meta:{changes:1}};
      },
    };
  }
}

class RunnerR2 {
  constructor(){this.objects=new Map();}
  async get(key){const value=this.objects.get(key);return value===undefined?null:{body:new Blob([value]).stream()};}
  async put(key,value,options={}){
    if(options.onlyIf?.get('If-None-Match')==='*'&&this.objects.has(key))return null;
    const raw=typeof value==='string'?value:await new Response(value).text();
    this.objects.set(key,raw);return {key};
  }
}

function env(status='QUEUED'){
  const artifacts=new RunnerR2();
  artifacts.objects.set(`jobs/${jobId}/snapshot.json`,snapshot);
  return {
    IGC_DB:new RunnerDB({job_id:jobId,case_id:'CAF-DEMO-001',owner_sub:'investigator-sub',snapshot_key:`jobs/${jobId}/snapshot.json`,snapshot_sha256:snapshotHash,case_version:1,status,result_key:null,error:null}),
    IGC_ARTIFACTS:artifacts,
    IGC_RUNNER_HMAC_SECRET:secret,
  };
}

async function signedRequest(method,action,body,envContext){
  const path=`/api/runner/jobs/${jobId}/${action}`;
  const timestamp=String(Math.floor(Date.now()/1000));
  const signature=await signRunnerRequest(envContext.IGC_RUNNER_HMAC_SECRET,timestamp,method,path,body);
  return new Request(`https://runner.test${path}`,{method,body:method==='POST'?body:undefined,headers:{'X-IGC-Timestamp':timestamp,'X-IGC-Signature':signature}});
}

const runner=createRunnerApi();

test('Runner only exposes its two routes and rejects unsigned snapshot requests before R2',async()=>{
  const e=env();
  const unsigned=await runner(new Request(`https://runner.test/api/runner/jobs/${jobId}/snapshot`),e);
  assert.equal(unsigned.status,401);
  assert.equal((await unsigned.text()).includes('PRIVATE_SNAPSHOT_MARKER'),false);
  assert.equal(e.IGC_ARTIFACTS.objects.size,1);
  for(const path of ['/', '/api/health', '/api/cases', '/api/admin']){
    const response=await runner(new Request(`https://runner.test${path}`),e);
    assert.equal(response.status,404,path);
  }
  const wrongSnapshotMethod=await runner(new Request(`https://runner.test/api/runner/jobs/${jobId}/snapshot`,{method:'POST',body:'{}'}),e);
  assert.equal(wrongSnapshotMethod.status,405);
  const wrongResultMethod=await runner(new Request(`https://runner.test/api/runner/jobs/${jobId}/result`),e);
  assert.equal(wrongResultMethod.status,405);
});

test('Invalid snapshot signature cannot read R2 content',async()=>{
  const e=env(),path=`/api/runner/jobs/${jobId}/snapshot`,timestamp=String(Math.floor(Date.now()/1000));
  const response=await runner(new Request(`https://runner.test${path}`,{headers:{'X-IGC-Timestamp':timestamp,'X-IGC-Signature':'v1='+'f'.repeat(64)}}),e);
  assert.equal(response.status,401);
  assert.equal((await response.text()).includes('PRIVATE_SNAPSHOT_MARKER'),false);
});

test('Valid signed snapshot preserves its immutable hash',async()=>{
  const e=env(),request=await signedRequest('GET','snapshot','',e);
  const response=await runner(request,e);
  assert.equal(response.status,200);
  assert.equal(response.headers.get('X-IGC-Snapshot-Sha256'),snapshotHash);
  assert.equal(await response.text(),snapshot);
});

test('A signed callback is persisted once; duplicate callbacks are rejected',async()=>{
  const e=env(),result={schema_version:'igc.arena_probe.v0.2',job_id:jobId,snapshot_sha256:snapshotHash,status:'PASS',modelica_executed:false,inference_calls:0,gates:{g1:'NOT_RUN',g2:'NOT_RUN',g3:'NOT_RUN'},probe_only:true,observable_count:1,issues:[]};
  const body=JSON.stringify(result),request=await signedRequest('POST','result',body,e);
  const first=await runner(request,e);
  assert.equal(first.status,200);
  assert.deepEqual(await first.json(),{accepted:true,status:'PASS'});
  assert.equal(e.IGC_DB.job.status,'COMPLETE');
  assert.equal(e.IGC_DB.job.result_key,`jobs/${jobId}/result.json`);
  assert.equal(e.IGC_ARTIFACTS.objects.get(`jobs/${jobId}/result.json`),body);

  const duplicate=await runner(await signedRequest('POST','result',body,e),e);
  assert.equal(duplicate.status,409);
  assert.equal(e.IGC_ARTIFACTS.objects.get(`jobs/${jobId}/result.json`),body);
});

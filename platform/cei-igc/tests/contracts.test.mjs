import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateDraft,validatePreflightReady,sha256} from '../src/domain.mjs';
import {signRunnerRequest,verifyRunnerRequest} from '../src/security.mjs';
import {createApi} from '../src/api.mjs';

const root=new URL('../',import.meta.url);
const template=JSON.parse(fs.readFileSync(new URL('../examples/investigation_intake_demo.json',import.meta.url)));
const proposal=JSON.parse(fs.readFileSync(new URL('../examples/arena_input_demo.json',import.meta.url)));
const clone=x=>JSON.parse(JSON.stringify(x));
const mockSecret='NOT_REAL_TEST_SECRET_32CHARS_LONG_2026';
class MockDB {
  constructor(){this.cases=new Map();this.jobs=new Map();}
  prepare(sql){let vals=[];const db=this;return {bind(...x){vals=x;return this;},async first(){
    if(sql.includes('FROM investigations')){const [id,owner]=vals;let r=db.cases.get(id);return r&&r.owner_sub===owner?clone(r):null;}
    if(sql.includes('FROM arena_jobs')){return clone(db.jobs.get(vals[0])||null);}
    throw new Error('Unsupported mock SELECT: '+sql);
  },async all(){
    if(sql.includes('FROM investigations'))return {results:[...db.cases.values()].filter(x=>x.owner_sub===vals[0]).map(x=>clone(x))};
    if(sql.includes('FROM arena_jobs'))return {results:[...db.jobs.values()].filter(x=>x.case_id===vals[0]&&x.owner_sub===vals[1]).map(x=>clone(x))};
    throw new Error('Unsupported mock list');
  },async run(){
    if(sql.startsWith('INSERT INTO investigations')){
      const [id,owner,intake,arena,created,updated]=vals;
      if(db.cases.has(id))throw new Error('duplicate');
      db.cases.set(id,{case_id:id,owner_sub:owner,intake_json:intake,arena_json:arena,version:1,created_at:created,updated_at:updated});return {meta:{changes:1}};
    }
    if(sql.startsWith('UPDATE investigations')){
      const [intake,arena,date,id,owner,version]=vals,r=db.cases.get(id);
      if(!r||r.owner_sub!==owner||r.version!==version)return {meta:{changes:0}};
      Object.assign(r,{intake_json:intake,arena_json:arena,version:version+1,updated_at:date});return {meta:{changes:1}};
    }
    if(sql.startsWith('INSERT INTO arena_jobs')){
      const [id,case_id,owner,snapshot_key,snapshot_sha256,case_version,created,updated]=vals;
      db.jobs.set(id,{job_id:id,case_id,owner_sub:owner,snapshot_key,snapshot_sha256,case_version,created_at:created,updated_at:updated,status:'DISPATCHING',github_run_id:null,github_url:null,result_key:null,error:null});return {meta:{changes:1}};
    }
    if(sql.includes("status='DISPATCH_ERROR'")){
      const [error,updated,id]=vals;Object.assign(db.jobs.get(id),{status:'DISPATCH_ERROR',error,updated_at:updated});return {meta:{changes:1}};
    }
    if(sql.includes("THEN 'QUEUED'")){
      const [rid,url,updated,id]=vals,r=db.jobs.get(id);
      if(!r)return {meta:{changes:0}};
      Object.assign(r,{status:r.status==='DISPATCHING'?'QUEUED':r.status,github_run_id:rid,github_url:url,updated_at:updated});return {meta:{changes:1}};
    }
    if(sql.includes('SET status=?,result_key=?')){
      const [status,result,updated,id]=vals;Object.assign(db.jobs.get(id),{status,result_key:result,updated_at:updated});return {meta:{changes:1}};
    }
    if(sql.includes('SET status=?,error=?')){
      const [status,error,updated,id]=vals;Object.assign(db.jobs.get(id),{status,error,updated_at:updated});return {meta:{changes:1}};
    }
    throw new Error('Unsupported mock statement: '+sql);
  }};}
}
class MockR2 {
  constructor(){this.map=new Map();}
  async put(key,value){this.map.set(key,typeof value==='string'?value:JSON.stringify(value));}
  async get(key){const s=this.map.get(key);return s==null?null:{body:new Blob([s]).stream()};}
}
const env=()=>({IGC_DB:new MockDB(),IGC_ARTIFACTS:new MockR2(),IGC_RUNNER_HMAC_SECRET:mockSecret,GITHUB_TOKEN:'NOT_REAL_GH_TOKEN',GITHUB_REPO:'yudocyudoc/short',GITHUB_WORKFLOW:'igc-arena-probe.yml',GITHUB_REF:'main'});
const req=(url,method='GET',body=null,headers={})=>new Request('https://local.test'+url,{method,headers:body?{'Content-Type':'application/json',...headers}:headers,body:body===null?undefined:JSON.stringify(body)});
const rpc=async(handler,request,ctx)=>{const response=await handler(request,ctx); const data=await response.json();return {status:response.status,data};};

test('V0.1 contract preserved and gold/holdout forbidden',()=>{
  assert.equal(validateDraft(clone(template),clone(proposal)).intake.case_id,'CAF-DEMO-001');
  assert.doesNotThrow(()=>validatePreflightReady(template));
  const a=clone(template);a.evidence.holdout.contents_included=true;
  assert.throws(()=>validateDraft(a),/reserva/);
  const b=clone(template);b.evidence.holdout.future_observation_data={value:8};
  assert.throws(()=>validateDraft(b),/reserva/);
  const c=clone(proposal);c.structure_proposals[0].validation.g2='PASS';
  assert.throws(()=>validateDraft(template,c),/G1–G3/);
});

test('Authenticated machine callback requires valid request-bound HMAC',async()=>{
  const path='/api/runner/jobs/234911ff-aaaa-4111-8999-bbbbbbbbbbbb/snapshot';
  const timestamp=String(Math.floor(Date.now()/1000));
  const sig=await signRunnerRequest(mockSecret,timestamp,'GET',path,'');
  const request=new Request('https://local.test'+path,{headers:{'X-IGC-Timestamp':timestamp,'X-IGC-Signature':sig}});
  await assert.doesNotReject(()=>verifyRunnerRequest(request,{IGC_RUNNER_HMAC_SECRET:mockSecret},''));
  const wrong=new Request('https://local.test'+path,{headers:{'X-IGC-Timestamp':timestamp,'X-IGC-Signature':'v1='+'f'.repeat(64)}});
  await assert.rejects(()=>verifyRunnerRequest(wrong,{IGC_RUNNER_HMAC_SECRET:mockSecret},''));
  assert.equal((await sha256('abc')).length,64);
});

test('Cloudflare D1+R2+GitHub dispatch+signed callback lifecycle with no AI',async()=>{
  const e=env(),calls=[];
  const githubFetch=async(url,options)=>{
    calls.push({url,body:options.body});
    return new Response(JSON.stringify({workflow_run_id:558210,run_url:'https://github.com/yudocyudoc/short/actions/runs/558210'}),{status:200,headers:{'Content-Type':'application/json'}});
  };
  const app=createApi({authorize:async()=>({sub:'investigator-01',email:'lab@example.com'}),requestFn:githubFetch});
  let r=await rpc(app,req('/api/cases','POST',{intake:template,arena:proposal}),e);
  assert.equal(r.status,201);assert.equal(r.data.version,1);
  r=await rpc(app,req('/api/cases/CAF-DEMO-001'),e);assert.equal(r.data.intake.evidence.holdout.contents_included,false);
  r=await rpc(app,req('/api/cases/CAF-DEMO-001','PUT',{expected_version:1,intake:template,arena:proposal}),e);
  assert.equal(r.data.version,2);
  r=await rpc(app,req('/api/cases/CAF-DEMO-001','PUT',{expected_version:1,intake:template,arena:proposal}),e);
  assert.equal(r.status,409);
  r=await rpc(app,req('/api/cases/CAF-DEMO-001/runs','POST',{kind:'COSTLY_IA'}),e);
  assert.equal(r.status,400);assert.equal(calls.length,0);
  r=await rpc(app,req('/api/cases/CAF-DEMO-001/runs','POST',{kind:'DETERMINISTIC_PROBE'}),e);
  assert.equal(r.status,202); assert.equal(calls.length,1);
  const dispatchBody=JSON.parse(calls[0].body);
  assert.deepEqual(Object.keys(dispatchBody).sort(),['inputs','ref']);
  assert.equal(dispatchBody.ref,'main');
  assert.equal(calls[0].body.includes('return_run_details'),false);
  const job=r.data.job_id;
  assert.equal(e.IGC_DB.jobs.get(job).github_run_id,558210);
  assert.equal(e.IGC_DB.jobs.get(job).github_url,'https://github.com/yudocyudoc/short/actions/runs/558210');
  const ts=String(Math.floor(Date.now()/1000));
  const path='/api/runner/jobs/'+job+'/snapshot';
  let signed=await signRunnerRequest(mockSecret,ts,'GET',path,'');
  const snapshotReq=new Request('https://local.test'+path,{headers:{'X-IGC-Timestamp':ts,'X-IGC-Signature':signed}});
  const snapshotResponse=await app(snapshotReq,e);assert.equal(snapshotResponse.status,200);
  const raw=await snapshotResponse.text();assert.equal(await sha256(raw),r.data.snapshot_sha256);
  const snap=JSON.parse(raw);assert.equal(snap.data_class,'VISIBLE_METADATA_ONLY');assert.equal(snap.holdout_contents_included,false);
  const result={schema_version:'igc.arena_probe.v0.2',job_id:job,snapshot_sha256:r.data.snapshot_sha256,status:'PASS',modelica_executed:false,inference_calls:0,gates:{g1:'NOT_RUN',g2:'NOT_RUN',g3:'NOT_RUN'},probe_only:true,observable_count:2,issues:[]};
  const resultPath='/api/runner/jobs/'+job+'/result',resultRaw=JSON.stringify(result);
  signed=await signRunnerRequest(mockSecret,ts,'POST',resultPath,resultRaw);
  const callback=new Request('https://local.test'+resultPath,{method:'POST',body:resultRaw,headers:{'X-IGC-Timestamp':ts,'X-IGC-Signature':signed}});
  r=await rpc(app,callback,e);assert.equal(r.status,200);
  r=await rpc(app,req('/api/runs/'+job),e);assert.equal(r.data.status,'COMPLETE');
  r=await rpc(app,req('/api/runs/'+job+'/result'),e);assert.equal(r.data.inference_calls,0);
});

test('A fast signed callback is not overwritten by the dispatch response',async()=>{
  const e=env();let app;
  const githubFetch=async(url,options)=>{
    const dispatch=JSON.parse(options.body),{job_id,snapshot_sha256}=dispatch.inputs;
    const timestamp=String(Math.floor(Date.now()/1000));
    const result={schema_version:'igc.arena_probe.v0.2',job_id,snapshot_sha256,status:'PASS',modelica_executed:false,inference_calls:0,gates:{g1:'NOT_RUN',g2:'NOT_RUN',g3:'NOT_RUN'},probe_only:true,observable_count:2,issues:[]};
    const resultPath='/api/runner/jobs/'+job_id+'/result',resultRaw=JSON.stringify(result);
    const signature=await signRunnerRequest(mockSecret,timestamp,'POST',resultPath,resultRaw);
    const callback=new Request('https://local.test'+resultPath,{method:'POST',body:resultRaw,headers:{'X-IGC-Timestamp':timestamp,'X-IGC-Signature':signature}});
    const callbackResponse=await app(callback,e);
    assert.equal(callbackResponse.status,200);
    return new Response(JSON.stringify({workflow_run_id:558211,run_url:'https://github.com/yudocyudoc/short/actions/runs/558211'}),{status:200,headers:{'Content-Type':'application/json'}});
  };
  app=createApi({authorize:async()=>({sub:'investigator-02'}),requestFn:githubFetch});
  let r=await rpc(app,req('/api/cases','POST',{intake:template,arena:proposal}),e);
  assert.equal(r.status,201);
  r=await rpc(app,req('/api/cases/CAF-DEMO-001/runs','POST',{kind:'DETERMINISTIC_PROBE'}),e);
  assert.equal(r.status,202);
  assert.equal(r.data.status,'COMPLETE');
  assert.equal(r.data.github_url,'https://github.com/yudocyudoc/short/actions/runs/558211');
  const job=e.IGC_DB.jobs.get(r.data.job_id);
  assert.equal(job.status,'COMPLETE');
  assert.equal(job.result_key,'jobs/'+r.data.job_id+'/result.json');
  assert.equal(job.github_run_id,558211);
});

test('GitHub auth check is read-only and does not expose credentials',async()=>{
  const e=env(),calls=[];
  const githubFetch=async(url,options)=>{
    calls.push({url,method:options.method||'GET',headers:options.headers,body:options.body});
    return new Response(JSON.stringify({ok:true}),{status:200,headers:{'Content-Type':'application/json'}});
  };
  const app=createApi({authorize:async()=>({sub:'investigator-03'}),requestFn:githubFetch});
  const r=await rpc(app,req('/api/github/auth-check'),e);
  assert.equal(r.status,200);
  assert.deepEqual(r.data,{authenticated:true,workflow_accessible:true});
  assert.deepEqual(calls.map(x=>[x.method,x.url]),[
    ['GET','https://api.github.com/user'],
    ['GET','https://api.github.com/repos/yudocyudoc/short/actions/workflows/igc-arena-probe.yml'],
  ]);
  assert.equal(calls.every(x=>x.body===undefined),true);
  assert.equal(calls[0].headers.Authorization,'Bearer '+e.GITHUB_TOKEN);
  assert.equal(JSON.stringify(r.data).includes(e.GITHUB_TOKEN),false);
});

test('GitHub authentication diagnostic distinguishes 401, 403, 404, and 422 safely',async()=>{
  for(const [status,diagnostic] of [
    [401,'invÃ¡lido, caducado o rechazado'],
    [403,'denegÃ³ el permiso'],
    [404,'no encontrado o recurso'],
    [422,'rechazÃ³ la solicitud por validaciÃ³n'],
  ]){
    const e=env(),calls=[];
    const app=createApi({authorize:async()=>({sub:'investigator-04'}),requestFn:async(url,options)=>{
      calls.push({url,method:options.method||'GET'});
      return new Response(JSON.stringify({message:'mock private detail'}),{status});
    }});
    const r=await rpc(app,req('/api/github/auth-check'),e);
    assert.equal(r.status,502);
    assert.match(r.data.error,new RegExp(`GitHub authentication check HTTP ${status}`));
    assert.ok(r.data.error.includes(diagnostic));
    assert.equal(calls.length,1);
    assert.equal(calls[0].url,'https://api.github.com/user');
    assert.equal(JSON.stringify(r.data).includes(e.GITHUB_TOKEN),false);
    assert.equal(JSON.stringify(r.data).includes('mock private detail'),false);
  }
});

test('Dispatch failure preserves GitHub status diagnosis without response details',async()=>{
  for(const [status,diagnostic] of [
    [401,'GITHUB_TOKEN invÃ¡lido'],
    [403,'denegÃ³ el permiso'],
    [404,'no encontrado o recurso'],
    [422,'workflow_dispatch, ref e inputs'],
  ]){
    const e=env();
    const app=createApi({authorize:async()=>({sub:'investigator-05'}),requestFn:async()=>
      new Response(JSON.stringify({message:'mock private GitHub response'}),{status})});
    await rpc(app,req('/api/cases','POST',{intake:template,arena:proposal}),e);
    const r=await rpc(app,req('/api/cases/CAF-DEMO-001/runs','POST',{kind:'DETERMINISTIC_PROBE'}),e);
    assert.equal(r.status,502);
    const job=[...e.IGC_DB.jobs.values()][0];
    assert.equal(job.status,'DISPATCH_ERROR');
    assert.ok(job.error.includes(`GitHub dispatch HTTP ${status}`));
    assert.ok(job.error.includes(diagnostic));
    assert.equal(job.error.includes('mock private GitHub response'),false);
    assert.equal(job.error.includes(e.GITHUB_TOKEN),false);
  }
});

test('Case ownership isolates API records',async()=>{
 const e=env();let who='owner-1';
 const app=createApi({authorize:async()=>({sub:who}),requestFn:async()=>new Response(null,{status:204})});
 await rpc(app,req('/api/cases','POST',{intake:template,arena:proposal}),e);
 who='owner-2';
 const r=await rpc(app,req('/api/cases/CAF-DEMO-001'),e);
 assert.equal(r.status,404);
 const ls=await rpc(app,req('/api/cases'),e);assert.equal(ls.data.items.length,0);
});


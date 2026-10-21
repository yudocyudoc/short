import {InputError,encode,sha256} from './domain.mjs';
export async function signRunnerRequest(secret,timestamp,method,path,body=''){
  if(typeof secret!=='string'||secret.length<24)throw new InputError('Secreto de runner no configurado',503);
  const hash=await sha256(body);
  const bytes=encode(`${timestamp}\n${method.toUpperCase()}\n${path}\n${hash}`);
  const key=await crypto.subtle.importKey('raw',encode(secret),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);
  const sig=new Uint8Array(await crypto.subtle.sign('HMAC',key,bytes));
  return 'v1='+[...sig].map(x=>x.toString(16).padStart(2,'0')).join('');
}
export async function verifyRunnerRequest(request,env,body=''){
  const timestamp=request.headers.get('X-IGC-Timestamp')||'';
  const signature=request.headers.get('X-IGC-Signature')||'';
  const seconds=Number(timestamp);
  if(!Number.isInteger(seconds)||Math.abs(Date.now()/1000-seconds)>300)throw new InputError('Firma vencida',401);
  const path=new URL(request.url).pathname;
  const expected=await signRunnerRequest(env.IGC_RUNNER_HMAC_SECRET,timestamp,request.method,path,body);
  if(!/^v1=[a-f0-9]{64}$/.test(signature))throw new InputError('Firma inválida',401);
  const key=await crypto.subtle.importKey('raw',encode(env.IGC_RUNNER_HMAC_SECRET),{name:'HMAC',hash:'SHA-256'},false,['verify']);
  const message=encode(`${timestamp}\n${request.method.toUpperCase()}\n${path}\n${await sha256(body)}`);
  const actual=new Uint8Array(signature.slice(3).match(/../g).map(x=>parseInt(x,16)));
  const ok=await crypto.subtle.verify('HMAC',key,actual,message);
  if(!ok||signature!==expected)throw new InputError('Firma inválida',401);
}


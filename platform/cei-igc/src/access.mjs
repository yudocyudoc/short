import {createRemoteJWKSet,jwtVerify} from 'jose';
import {InputError} from './domain.mjs';
const jwksCache=new Map();
function accessDomain(env) {
  const team=env.ACCESS_TEAM_DOMAIN||'';
  if(!/^[a-zA-Z0-9.-]+\.cloudflareaccess\.com$/.test(team))throw new InputError('Access no configurado',503);
  if(!env.ACCESS_AUD || env.ACCESS_AUD.startsWith('REPLACE_'))throw new InputError('Access audience no configurado',503);
  return 'https://'+team;
}
export async function authorizeAccess(request,env){
  const issuer=accessDomain(env);
  let token=request.headers.get('Cf-Access-Jwt-Assertion');
  if(!token){
    const cookie=request.headers.get('Cookie')||'';
    const match=cookie.match(/(?:^|;\s*)CF_Authorization=([^;]+)/);
    if(match)token=decodeURIComponent(match[1]);
  }
  if(!token)throw new InputError('Requiere autenticación de Cloudflare Access',401);
  if(!jwksCache.has(issuer))jwksCache.set(issuer,createRemoteJWKSet(new URL(issuer+'/cdn-cgi/access/certs')));
  try{
    const {payload}=await jwtVerify(token,jwksCache.get(issuer),{issuer,audience:env.ACCESS_AUD});
    if(typeof payload.sub!=='string' || !payload.sub)throw new Error('sub missing');
    return {sub:payload.sub,email:payload.email||null};
  }catch{throw new InputError('JWT de Access inválido o caducado',401);}
}


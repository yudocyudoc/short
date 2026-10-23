import {createApi} from './api.mjs';
import {authorizeAccess} from './access.mjs';
const api=createApi({authorize:authorizeAccess});
export default {
  async fetch(request,env){
    const pathname=new URL(request.url).pathname;
    if(pathname.startsWith('/api/'))return api(request,env);
    return env.ASSETS.fetch(request);
  }
};


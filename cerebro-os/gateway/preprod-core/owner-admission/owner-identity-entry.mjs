// Owner identity proof only; does not issue a grant, reserve an order or dispatch.
import {verifyOwnerIdentity} from './owner-admission.mjs';
const reply=(body,status)=>new Response(JSON.stringify(body),{status,headers:{'content-type':'application/json; charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff','content-security-policy':"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"}});
export default {async fetch(request,env){
 const u=new URL(request.url);
 if(env.OWNER_PROBE_ENABLED!=='true'||env.CORE_ENV!=='PREPROD'||u.pathname!=='/identity'||u.search||request.method!=='GET')return reply({status:'CLOSED'},404);
 try{const a=await verifyOwnerIdentity(request,env);return reply({status:'OWNER_IDENTITY_PREPROD_VERIFIED',environment:'PREPROD',principal_id:'iam:owner',subject_sha256:a.subject_sha256,audience_sha256:a.audience_sha256,verified_at_epoch:a.verified_at_epoch,expires_at_epoch:a.expires_at_epoch,dispatch_authorized:false,promotion_allowed:false},200);}
 catch{return reply({status:'ACCESS_DENIED'},403);}
}};

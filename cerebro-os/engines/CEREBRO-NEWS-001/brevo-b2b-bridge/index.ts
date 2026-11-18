import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {audit,allowed} from "./core.mjs";
function out(x:unknown,status=200){return new Response(JSON.stringify(x),{status,headers:{"content-type":"application/json","cache-control":"no-store"}});}
Deno.serve(async(req:Request)=>{
 if(req.method!=="GET")return out({status:"METHOD_NOT_ALLOWED"},405);
 const u=new URL(req.url);
 if(u.pathname.endsWith("/health"))return out({state:"LAB_OFF",version:"0.3.0",send_authorized:false});
 if(!u.pathname.endsWith("/audit"))return out({state:"NOT_FOUND"},404);
 if(Deno.env.get("NEWS001_BREVO_AUDIT_ENABLED")!=="true")return out({state:"AUDIT_DISABLED",send_authorized:false},423);
 // Supabase JWT gateway must be enabled. Additionally require exact server credential.
 const serverKey=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")||"";
 if(!serverKey||req.headers.get("authorization")!=="Bearer "+serverKey)return out({state:"FORBIDDEN"},403);
 const brevoKey=Deno.env.get("BREVO_API_KEY")||"";
 if(!brevoKey)return out({state:"BREVO_KEY_MISSING"},503);
 const read=async(path:string)=>{
  if(!allowed(path))throw new Error("UNSAFE_PATH");
  const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),7500);
  try {
   const response=await fetch("https://api.brevo.com/v3"+path,{method:"GET",redirect:"error",
      headers:{"api-key":brevoKey,"accept":"application/json"},signal:controller.signal});
   if(!response.ok)throw new Error("BREVO_HTTP_"+response.status);
   const raw=await response.text();if(raw.length>1000000)throw new Error("BREVO_PAYLOAD_TOO_BIG");
   return JSON.parse(raw);
  }finally{clearTimeout(timer);}
 };
 try{return out(await audit(read));}
 catch(e){const msg=e instanceof Error?e.message:"UNKNOWN";return out({state:"FAILED_CLOSED",
   error_code:/^(BREVO_HTTP_\d{3}|UNSAFE_PATH|BAD_API_RESPONSE|BAD_CONTACT_ID|PAGINATION_LIMIT)$/.test(msg)?msg:"UPSTREAM_FAILURE",send_authorized:false},503);}
});

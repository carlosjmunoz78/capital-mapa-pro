// PREPROD owner admission only; never grants execution or promotion.
const deny=code=>{throw Error(code)};
const enc=new TextEncoder();
const bytes=s=>{if(typeof s!=='string'||! /^[A-Za-z0-9_-]+$/.test(s))deny('TOKEN_FORMAT');return Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(s.length/4)*4,'=')),x=>x.charCodeAt(0));};
const part=s=>JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes(s)));
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const digest=async s=>hex(await crypto.subtle.digest('SHA-256',enc.encode(s)));
async function boundedText(stream,limit,code){
 if(!stream)deny(code);const reader=stream.getReader();let size=0;const decoder=new TextDecoder('utf-8',{fatal:true});let result='';
 try{for(;;){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>limit)deny(code);result+=decoder.decode(value,{stream:true});}return result+decoder.decode();}
 finally{await reader.cancel().catch(()=>{});reader.releaseLock();}
}
export async function verifyOwnerIdentity(request,env){
 const {CORE_ENV,ACCESS_ISSUER,ACCESS_AUD,ACCESS_LAB_AUD,ACCESS_OWNER_EMAIL,ACCESS_OWNER_SUB,ACCESS_ORIGIN}=env;
 if(CORE_ENV!=='PREPROD'||!/^https:\/\/[a-z0-9-]+\.cloudflareaccess\.com$/.test(ACCESS_ISSUER??'')||!ACCESS_AUD||!ACCESS_LAB_AUD||ACCESS_AUD===ACCESS_LAB_AUD||!ACCESS_OWNER_EMAIL||!ACCESS_OWNER_SUB||!ACCESS_ORIGIN)deny('PREPROD_ACCESS_CONFIG');
 if(new URL(request.url).origin!==ACCESS_ORIGIN)deny('REQUEST_ORIGIN_DENIED');
 const token=request.headers.get('Cf-Access-Jwt-Assertion');if(!token||token.length>12000||token.split('.').length!==3)deny('ACCESS_REQUIRED');
 const [h,p,s]=token.split('.'),head=part(h),c=part(p),now=Math.floor(Date.now()/1000);
 if(head.alg!=='RS256'||typeof head.kid!=='string'||! /^[A-Za-z0-9_-]{1,128}$/.test(head.kid)||c.iss!==ACCESS_ISSUER||!Array.isArray(c.aud)||c.aud.length!==1||c.aud[0]!==ACCESS_AUD||c.sub!==ACCESS_OWNER_SUB||typeof c.email!=='string'||c.email.toLowerCase()!==ACCESS_OWNER_EMAIL.toLowerCase()||c.type!=='app')deny('ACCESS_SCOPE');
 if(!Number.isSafeInteger(c.iat)||!Number.isSafeInteger(c.exp)||c.iat>now+30||c.exp<=now||c.exp<=c.iat||c.exp-c.iat>3600||(c.nbf!==undefined&&(!Number.isSafeInteger(c.nbf)||c.nbf>now+30)))deny('ACCESS_EXPIRED');
 const res=await fetch(ACCESS_ISSUER+'/cdn-cgi/access/certs',{method:'GET',redirect:'manual',headers:{Accept:'application/json'},signal:AbortSignal.timeout(8000)});
 if(!res.ok||res.redirected||Number(res.headers.get('content-length')||0)>65536)deny('CERT_FETCH');
 const raw=await boundedText(res.body,65536,'CERT_TOO_LARGE');
 const keys=JSON.parse(raw).keys;if(!Array.isArray(keys)||keys.length===0||keys.length>32)deny('CERT_FORMAT');
 const matches=keys.filter(k=>k?.kid===head.kid);if(matches.length!==1||matches[0].kty!=='RSA'||(matches[0].use&&matches[0].use!=='sig')||(matches[0].alg&&matches[0].alg!=='RS256'))deny('CERT_KEY');
 const key=await crypto.subtle.importKey('jwk',matches[0],{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['verify']);
 if(key.algorithm.modulusLength<2048||!await crypto.subtle.verify('RSASSA-PKCS1-v1_5',key,bytes(s),enc.encode(h+'.'+p)))deny('ACCESS_SIGNATURE');
 if(c.exp<=Math.floor(Date.now()/1000))deny('ACCESS_EXPIRED');
 return Object.freeze({subject_sha256:await digest(c.sub),audience_sha256:await digest(ACCESS_AUD),verified_at_epoch:now,expires_at_epoch:Math.min(c.exp,now+120)});
}
export async function admitOwner(request,env){
 if(request.method!=='POST'||request.headers.get('origin')!==env.ACCESS_ORIGIN||request.headers.get('content-type')!=='application/json')deny('REQUEST_ORIGIN_DENIED');
 const identity=await verifyOwnerIdentity(request,env);
 const body=await boundedText(request.body,1024,'ORDER_SIZE');const q=JSON.parse(body);
 const expected={company_id:'fenix',engine_id:'FACT-001',environment:'PREPROD',version:'1.1.0',capability:'FACT.INVENTORY.READ',request_id:q?.request_id};
 if(!q||typeof q!=='object'||Array.isArray(q)||!/^CORE-PREPROD-20261124-00[2-8]$/.test(q.request_id??'')||Object.keys(q).length!==Object.keys(expected).length||Object.entries(expected).some(([k,v])=>q[k]!==v))deny('ORDER_SCOPE');
 // Ledger/issuer is intentionally a separate boundary; this receipt cannot authorize dispatch.
 return Object.freeze({schema:'cerebro.core.owner-admission.v1',status:'OWNER_IDENTITY_VERIFIED_ONLY',principal_id:'iam:owner',...identity,request_sha256:await digest(JSON.stringify(expected)),route:expected,dispatch_authorized:false,promotion_allowed:false});
}

// Parallel bounded CP131 integration. No HTTP endpoints, no deployment.
import {command,signBody,verifyBody,verifyCurrentGrant,scope,principal,issuer} from '../cp169/independent-iam.mjs';
import {requestId} from '../cp169/bounded-store.mjs';
import {createFact} from '../cp169/private-clients.mjs';
import {cp131Scope,createFactReceiptPort,createJarvisReceiptPort} from '../cp176/receipt-ports.mjs';
const enc=new TextEncoder(),now=()=>Math.floor(Date.now()/1000);
const fail=s=>{throw Error(s)};
const hex=b=>Array.from(new Uint8Array(b),v=>v.toString(16).padStart(2,'0')).join('');
const unhex=s=>Uint8Array.from(s.match(/../g),x=>parseInt(x,16));
const canonical=x=>enc.encode(JSON.stringify(x,Object.keys(x).sort()));
const hash=async x=>hex(await crypto.subtle.digest('SHA-256',enc.encode(JSON.stringify(x))));
const ref='policy://cp166/'+requestId;
const req=Object.freeze({...cp131Scope,request_id:requestId,principal_id:principal,policy_receipt_ref:ref});
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const same=(a,b)=>a?.mac===b?.mac&&exact(a?.body,b?.body??{});
const macKey=k=>k?.type==='secret'&&k.algorithm?.name==='HMAC'&&k.algorithm?.hash?.name==='SHA-256'&&k.algorithm?.length===256&&!k.extractable&&k.usages.includes('verify');
async function checkMac(k,r){return !!r?.body&&typeof r.mac==='string'&&/^[0-9a-f]{64}$/.test(r.mac)&&crypto.subtle.verify('HMAC',k,unhex(r.mac),canonical(r.body));}
export function createFactService({db,iam,jarvisPublic,authorityPublic,factPrivate,receiptKey,store,clock=now}={}){
 if(typeof store?.get!=='function'||typeof store?.insertOnce!=='function')fail('FACT_STORE_REQUIRED');
 const reader=createFact({db,iam,jarvisPublic,authorityPublic,factPrivate,clock});
 const receipts=createFactReceiptPort({key:receiptKey,principal,store,clock});
 return Object.freeze({async read(r,sig){const out=await reader.read(r,sig);const f=await receipts.record(req,await hash(out.result));return {...out,cp131:f};},
 async current(nonce){const c=command('current',requestId,nonce,clock());return iam.current(c,await signBody(factPrivate,c));},
 async persisted(id){if(id!==requestId)fail('FACT_READBACK_SCOPE');return store.get(id);}
 });
}
export function createTribunal({jarvisVerifyKey,factVerifyKey,authorityPublic,factReader,clock=now}={}){
 if(!macKey(jarvisVerifyKey)||!macKey(factVerifyKey)||!authorityPublic||typeof factReader?.current!=='function'||typeof factReader?.persisted!=='function')fail('TRIBUNAL_PORTS_REQUIRED');
 return Object.freeze({async verify(j,f){
 const t=clock(),jtime=j?.body?.emitted_at_epoch,ftime=f?.body?.emitted_at_epoch,h=f?.body?.result_sha256;
 if(!Number.isSafeInteger(t)||![jtime,ftime].every(v=>Number.isSafeInteger(v)&&v<=t&&t-v<=300)||typeof h!=='string'||!/^[0-9a-f]{64}$/.test(h)||!exact(j.body,{...req,emitted_at_epoch:jtime,origin:'JARVIS',target:'FACT-001',owner_access_verified:true,iam_policy:'ALLOW_READ_ONLY'})||!exact(f.body,{...req,emitted_at_epoch:ftime,origin:'FACT-001',target:'JARVIS',status:'COMPLETED',result_sha256:h}))fail('PAIR_SCOPE_DENIED');
 // Both service keys must be distinct. A valid MAC under the other role is disallowed.
 if(!await checkMac(jarvisVerifyKey,j)||!await checkMac(factVerifyKey,f)||await checkMac(jarvisVerifyKey,f)||await checkMac(factVerifyKey,j))fail('PAIR_MAC_DENIED');
 const nonce=crypto.randomUUID(),e=await factReader.current(nonce);
 const g=await verifyCurrentGrant({envelope:e,authorityPublicKey:authorityPublic,requestId,readerNonce:nonce,now:clock()});
 if(g.policy_receipt_ref!==ref||g.issuer_id!==issuer||g.principal_id!==principal||![jtime,ftime].every(v=>v>=g.issued_at_epoch&&v<g.expires_at_epoch))fail('GRANT_BINDING_DENIED');
 const stored=await factReader.persisted(requestId);
 if(!same(stored,f))fail('PERSISTED_RECEIPT_DENIED');
 const end=clock();if(end>=g.expires_at_epoch||end-g.checked_at_epoch>10)fail('GRANT_FRESHNESS_DENIED');
 return {status:'VERIFIED_AUTHORIZED_PAIR',iam_grant_verified:true,request_id:requestId,promotion_allowed:false};
 }});
}
export function createBoundedJarvis({iam,fact,tribunal,jarvisPrivate,factPublic,receiptKey,store,ownerAccess,clock=now}={}){
 if(typeof iam?.issue!=='function'||typeof iam?.revoke!=='function'||typeof fact?.read!=='function'||typeof tribunal?.verify!=='function'||typeof ownerAccess!=='function')fail('RUNTIME_PORTS_REQUIRED');
 const receipts=createJarvisReceiptPort({key:receiptKey,principal,store,ownerAccess,clock});
 return Object.freeze({async run(){
 if(await ownerAccess(req)!==true)fail('OWNER_ACCESS_DENIED');
 let verified,out;
 try{
 const c=command('issue',requestId,crypto.randomUUID(),clock());const g=await iam.issue(c,await signBody(jarvisPrivate,c));if(g.policy_receipt_ref!==ref)fail('GRANT_REFERENCE_DENIED');
 const j=await receipts.record(req);
 const r={...scope,request_id:requestId,principal_id:principal,policy_receipt_ref:ref,version:'1.0.0',emitted_at_epoch:clock()};
 out=await fact.read(r,await signBody(jarvisPrivate,r));
 if(!await verifyBody(factPublic,out.receipt,out.signature)||out.receipt.result_sha256!==await hash(out.result)||out.cp131?.body?.result_sha256!==out.receipt.result_sha256||out.result.company_id!=='fenix'||out.result.environment!=='LAB'||out.result.request_id!==requestId)fail('FACT_RESULT_DENIED');
 verified=await tribunal.verify(j,out.cp131);
 if(verified?.status!=='VERIFIED_AUTHORIZED_PAIR'||verified.iam_grant_verified!==true||verified.request_id!==requestId||verified.promotion_allowed!==false)fail('TRIBUNAL_DENIED');
 }finally{const c=command('revoke',requestId,crypto.randomUUID(),clock());const v=await iam.revoke(c,await signBody(jarvisPrivate,c));if(v.state!=='REVOKED')fail('REVOCATION_NOT_CONFIRMED');}
 return {status:'CP177_PAIR_VERIFIED_AND_REVOKED',result:out.result,grant_revoked:true,promotion_allowed:false};
 }});
}

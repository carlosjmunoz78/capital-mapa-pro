// Scoped PREPROD provenance, not an execution grant. Private signing key stays with issuer.
import {admitOwner} from './owner-admission.mjs';
import {signBody,verifyBody} from '../../../factory/cp169/independent-iam.mjs';
const fail=s=>{throw Error(s)}, now=()=>Math.floor(Date.now()/1000);
const hex=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([k,v])=>a[k]===v);
const hash=async x=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(x))),v=>v.toString(16).padStart(2,'0')).join('');
const route=id=>({company_id:'fenix',engine_id:'FACT-001',environment:'PREPROD',version:'1.1.0',capability:'FACT.INVENTORY.READ',request_id:id});
const scope=id=>typeof id==='string'&&/^CORE-PREPROD-20261124-00[2-8]$/.test(id);
const canonical=b=>JSON.stringify(b,Object.keys(b).sort());
const envelopeHash=e=>hash(canonical(e.body)+'.'+e.signature);
function body(a){return {...route(a.route.request_id),schema:'cerebro.core.owner-origin.v1',issuer:'iam:owner-admission-preprod',principal_id:'iam:owner',subject_sha256:a.subject_sha256,audience_sha256:a.audience_sha256,request_sha256:a.request_sha256,verified_at_epoch:a.verified_at_epoch,expires_at_epoch:a.expires_at_epoch,nonce:crypto.randomUUID(),dispatch_authorized:false,promotion_allowed:false};}
async function validate(e,pub,env,id){
 const b=e?.body,t=now();
 if(env.CORE_ENV!=='PREPROD'||!scope(id)||!b||!exact(e,{body:b,signature:e.signature})||!exact(b,{...route(id),schema:'cerebro.core.owner-origin.v1',issuer:'iam:owner-admission-preprod',principal_id:'iam:owner',subject_sha256:b.subject_sha256,audience_sha256:b.audience_sha256,request_sha256:b.request_sha256,verified_at_epoch:b.verified_at_epoch,expires_at_epoch:b.expires_at_epoch,nonce:b.nonce,dispatch_authorized:false,promotion_allowed:false})||!hex(b.subject_sha256)||!hex(b.audience_sha256)||!hex(b.request_sha256)||!/^[-a-f0-9]{36}$/.test(b.nonce??'')||!Number.isSafeInteger(b.verified_at_epoch)||!Number.isSafeInteger(b.expires_at_epoch)||b.verified_at_epoch>t||b.expires_at_epoch<=t||b.expires_at_epoch-b.verified_at_epoch>120)fail('OWNER_RECEIPT_SCOPE');
 if(!env.ACCESS_OWNER_SUB||!env.ACCESS_AUD||env.ACCESS_AUD===env.ACCESS_LAB_AUD||b.subject_sha256!==await hash(env.ACCESS_OWNER_SUB)||b.audience_sha256!==await hash(env.ACCESS_AUD)||b.request_sha256!==await hash(JSON.stringify(route(id)))||!await verifyBody(pub,b,e.signature)||b.expires_at_epoch<=now())fail('OWNER_RECEIPT_SIGNATURE');
 return b;
}
// storage must be isolated SQLite durable storage, with synchronous atomic transactions.
// No delete/reset method: ambiguous or expired reservations stay consumed or held.
export function ownerLedger(storage){
 if(!storage?.sql||typeof storage.transactionSync!=='function')fail('OWNER_LEDGER_CONFIG');
 const sql=storage.sql;sql.exec('CREATE TABLE IF NOT EXISTS owner_origin_v1 (request_id TEXT PRIMARY KEY, receipt_hash TEXT NOT NULL, expires INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN (\'RESERVED\',\'CONSUMED\')))'); 
 const row=id=>sql.exec('SELECT request_id,receipt_hash,expires,state FROM owner_origin_v1 WHERE request_id=?',id).toArray()[0];
 return Object.freeze({
 reserve(id,h,exp){return storage.transactionSync(()=>{if(!scope(id)||!hex(h)||!Number.isSafeInteger(exp)||exp<=now()||row(id))fail('OWNER_RESERVATION_DENIED');sql.exec("INSERT INTO owner_origin_v1 VALUES (?,?,?,'RESERVED')",id,h,exp);return true;});},
 consume(id,h){return storage.transactionSync(()=>{const r=row(id);if(!r||r.receipt_hash!==h||r.expires<=now()||r.state!=='RESERVED')fail('OWNER_REPLAY_OR_MISSING');sql.exec("UPDATE owner_origin_v1 SET state='CONSUMED' WHERE request_id=? AND state='RESERVED'",id);if(row(id)?.state!=='CONSUMED')fail('OWNER_LEDGER_DRIFT');return true;});},
 status(id){const r=row(id);return r?Object.freeze({...r}):null;}
 });
}
export async function issueOwnerOrigin(request,env,{signingKey,publicKey,ledger}){
 const a=await admitOwner(request,env),b=body(a);
 const e={body:b,signature:await signBody(signingKey,b)};
 await validate(e,publicKey,env,b.request_id);
 ledger.reserve(b.request_id,await envelopeHash(e),b.expires_at_epoch);
 return e;
}
export async function consumeOwnerOrigin(e,env,{publicKey,ledger,requestId}){
 const b=await validate(e,publicKey,env,requestId),h=await envelopeHash(e);
 ledger.consume(requestId,h);
 return Object.freeze({status:'OWNER_ORIGIN_CONSUMED',request_id:requestId,receipt_sha256:h,principal_id:b.principal_id,dispatch_authorized:false,promotion_allowed:false});
}

// Candidate contract review only: no IAM grant issuer, execution, ingress or deployment.
import {verifyBody} from '../../factory/cp169/independent-iam.mjs';
export const catalogGrantScope=Object.freeze({company_id:'fenix',engine_id:'FACT-001',
 environment:'PROD',version:'1.2.0',capability:'FACT.CATALOG.READ',read_only:true,
 external_mutation_allowed:false,cost_ceiling_eur:0});
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{8,128}$/.test(x);
const ref=x=>typeof x==='string'&&/^[A-Za-z0-9_.:/-]{8,200}$/.test(x);
const key=k=>k?.type==='public'&&k.algorithm?.name==='Ed25519'&&k.usages.includes('verify');
const raw=async k=>Array.from(new Uint8Array(await crypto.subtle.exportKey('raw',k))).join(',');
const exact=(a,b)=>a&&Object.getPrototypeOf(a)===Object.prototype&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([k,v])=>Object.hasOwn(a,k)&&a[k]===v);
const denied=reason=>Object.freeze({status:'BLOCKED',reason,execution_allowed:false,deployment_authorized:false});
const clock=()=>Math.floor(Date.now()/1000);
export async function createCatalogGrantReviewer({issuerId,principalId,readerId,authorityPublicKey,
 principalPublicKey,readerPublicKey,now=clock}={}){
 if(![issuerId,principalId,readerId].every(id)||new Set([issuerId,principalId,readerId]).size!==3||
 ![authorityPublicKey,principalPublicKey,readerPublicKey].every(key)||typeof now!=='function')
 throw Error('TRUST_CONFIG_DENIED');
 const keys=await Promise.all([authorityPublicKey,principalPublicKey,readerPublicKey].map(raw));
 if(new Set(keys).size!==3)throw Error('KEY_SEPARATION_DENIED');
 return async function review({envelope,requestId,readerNonce,policyReceiptRef}={}){
  try{
   if(!id(requestId)||!id(readerNonce)||!ref(policyReceiptRef))return denied('REFERENCE_DENIED');
   const e=structuredClone(envelope),b=e?.body;
   if(!exact(e,{body:b,signature:e?.signature})||!b)return denied('ENVELOPE_DENIED');
   const expected={...catalogGrantScope,issuer_id:issuerId,principal_id:principalId,
    reader_id:readerId,request_id:requestId,reader_nonce:readerNonce,policy_receipt_ref:policyReceiptRef,
    decision:'ALLOW_READ_ONLY',active:true,revoked:false,issued_at_epoch:b.issued_at_epoch,
    expires_at_epoch:b.expires_at_epoch,checked_at_epoch:b.checked_at_epoch};
   if(!exact(b,expected))return denied('GRANT_SCOPE_DENIED');
   const fresh=t=>[t,b.issued_at_epoch,b.checked_at_epoch,b.expires_at_epoch].every(Number.isSafeInteger)&&
    0<=b.issued_at_epoch&&b.issued_at_epoch<=b.checked_at_epoch&&b.checked_at_epoch<=t&&
    t<b.expires_at_epoch&&b.expires_at_epoch-b.issued_at_epoch===120&&t-b.checked_at_epoch<=10;
   if(!fresh(now()))return denied('GRANT_FRESHNESS_DENIED');
   if(!await verifyBody(authorityPublicKey,b,e.signature)||!fresh(now()))
    return denied('SIGNATURE_OR_FRESHNESS_DENIED');
   // Cryptographic review is evidence, not runtime admission or production release.
   return Object.freeze({status:'GRANT_EVIDENCE_VERIFIED',request_id:requestId,
    environment:'PROD',execution_allowed:false,deployment_authorized:false});
  }catch{return denied('GRANT_REVIEW_UNAVAILABLE');}
 };
}

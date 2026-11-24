// CP168 private clients. No HTTP operation, publication, or production scope.
import {command,signBody,verifyBody,verifyCurrentGrant,scope,principal,issuer} from './independent-iam.mjs';
import {requestId,assertCanaryId} from './bounded-store.mjs';
import {createFactoryCandidateReader} from '../cp162/fact001_inventory_read_cp162.mjs';
const now=()=>Math.floor(Date.now()/1000);
const enc=new TextEncoder();
const digest=async x=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(JSON.stringify(x)))),b=>b.toString(16).padStart(2,'0')).join('');
const fail=s=>{throw Error(s)};
export function createFact({db,iam,jarvisPublic,authorityPublic,factPrivate,clock=now,canaryId=requestId}={}){
 const requestId=assertCanaryId(canaryId),ref='policy://cp166/'+requestId;
 if(!iam||typeof iam.current!=='function')fail('AUTHORITY_REQUIRED');
 return Object.freeze({async read(r,sig){
  if(r?.request_id!==requestId||r?.policy_receipt_ref!==ref)fail('CANARY_SCOPE_DENIED');
  const read=createFactoryCandidateReader({db,authenticateJarvis:(q,p)=>verifyBody(jarvisPublic,q,p),readCurrentGrant:async(refIn)=>{
   if(refIn!==ref)fail('REF_DENIED');const c=command('current',requestId,crypto.randomUUID(),clock());const e=await iam.current(c,await signBody(factPrivate,c));return verifyCurrentGrant({envelope:e,authorityPublicKey:authorityPublic,requestId,readerNonce:c.nonce,now:clock()});
  },principalId:principal,issuerId:issuer,clock});
  const result=await read(r,sig);
  const receipt={...scope,request_id:requestId,principal_id:principal,policy_receipt_ref:ref,version:'1.0.0',origin:'FACT-001',target:'JARVIS',status:'COMPLETED',emitted_at_epoch:clock(),result_sha256:await digest(result)};
  return {result,receipt,signature:await signBody(factPrivate,receipt)};
 }});
}
export function createJarvis({iam,fact,jarvisPrivate,factPublic,clock=now,canaryId=requestId}={}){
 const requestId=assertCanaryId(canaryId),ref='policy://cp166/'+requestId;
 if(!iam||typeof iam.issue!=='function'||typeof iam.revoke!=='function'||!fact||typeof fact.read!=='function')fail('PRIVATE_PORTS_REQUIRED');
 return Object.freeze({async run(){
  const issue=command('issue',requestId,crypto.randomUUID(),clock());
  const g=await iam.issue(issue,await signBody(jarvisPrivate,issue));
  let result,receipt;
  try{
   if(g.policy_receipt_ref!==ref)fail('GRANT_REF_DENIED');
   const r={...scope,request_id:requestId,principal_id:principal,policy_receipt_ref:ref,version:'1.0.0',emitted_at_epoch:clock()};
   const sig=await signBody(jarvisPrivate,r);
   const out=await fact.read(r,sig);
   if(!await verifyBody(factPublic,out.receipt,out.signature)||out.receipt.request_id!==requestId||out.receipt.policy_receipt_ref!==ref||out.receipt.origin!=='FACT-001'||out.receipt.target!=='JARVIS'||out.receipt.status!=='COMPLETED'||out.receipt.result_sha256!==await digest(out.result)||out.result.company_id!=='fenix'||out.result.environment!=='LAB')fail('FACT_RECEIPT_DENIED');
   result=out.result;receipt=out.receipt;
  }finally{const c=command('revoke',requestId,crypto.randomUUID(),clock());const state=await iam.revoke(c,await signBody(jarvisPrivate,c));if(state.state!=='REVOKED')fail('REVOCATION_FAILED');}
  return {status:'INDEPENDENT_IAM_CANDIDATE_READ_PASS',result,receipt,grant_revoked:true,receipt_persisted:false,production_authorized:false};
 }});
}

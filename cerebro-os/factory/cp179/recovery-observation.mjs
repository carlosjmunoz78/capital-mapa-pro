// CP179 additive recovery observation. No issuance, mutation, reset or retry.
import {scope,issuer,principal,signBody,verifyBody} from '../cp169/independent-iam.mjs';
const now=()=>Math.floor(Date.now()/1000),enc=new TextEncoder();
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{8,128}$/.test(x);
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const canonical=o=>enc.encode(JSON.stringify(o,Object.keys(o).sort()));
const digest=async o=>hex(await crypto.subtle.digest('SHA-256',canonical(o)));
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const safe=n=>Number.isSafeInteger(n)&&n>=0;
const fresh=(n,t)=>safe(n)&&safe(t)&&n<=t&&t-n<=10;
const key=k=>k?.type==='public'&&k.algorithm?.name==='Ed25519'&&k.usages.includes('verify');
const base=(requestId,nonce,ledgerHash)=>({schema:'cerebro.recovery-observation.v1',...scope,request_id:requestId,nonce,ledger_sha256:ledgerHash});
const hold=reason=>({status:'HOLD_RECOVERY',reason,retry_allowed:false,promotion_allowed:false});
function ledgerValid(r,id){return r&&exact(r,{request_id:id,state:r.state,created:r.created,terminal:r.terminal})&&['RUNNING','HOLD'].includes(r.state)&&safe(r.created)&&(r.state==='RUNNING'?r.terminal===null:safe(r.terminal)&&r.terminal>=r.created);}
function revokedGrant(g,requestId,t){return g&&exact(g,{...scope,issuer_id:issuer,principal_id:principal,request_id:requestId,policy_receipt_ref:'policy://cp166/'+requestId,version:'1.0.0',decision:'ALLOW_READ_ONLY',active:false,revoked:true,issued_at_epoch:g.issued_at_epoch,expires_at_epoch:g.expires_at_epoch})&&safe(g.issued_at_epoch)&&safe(g.expires_at_epoch)&&g.issued_at_epoch<=t&&g.expires_at_epoch-g.issued_at_epoch===120;}
export function createRevocationAttester({requestId,readGrant,signingKey,clock=now}={}){
 if(!id(requestId)||typeof readGrant!=='function'||typeof clock!=='function'||signingKey?.type!=='private'||signingKey.algorithm?.name!=='Ed25519'||signingKey.extractable||!signingKey.usages.includes('sign'))throw Error('AUTHORITY_READ_PORT_DENIED');
 return Object.freeze({async attest(q){
  if(!id(q?.nonce)||typeof q?.ledger_sha256!=='string'||!/^[0-9a-f]{64}$/.test(q.ledger_sha256)||!exact(q,base(requestId,q.nonce,q.ledger_sha256)))throw Error('RECOVERY_SCOPE_DENIED');
  const g=await readGrant(requestId),t=clock();
  // Absence/expiry/active state never implies revocation.
  if(!revokedGrant(g,requestId,t))throw Error('REVOCATION_NOT_ESTABLISHED');
  const body={...q,role:'IAM',issuer_id:issuer,principal_id:principal,active:false,revoked:true,grant_sha256:await digest(g),issued_at_epoch:g.issued_at_epoch,expires_at_epoch:g.expires_at_epoch,checked_at_epoch:t};
  return {body,signature:await signBody(signingKey,body)};
 }});
}
export function createRecoveryInspector({requestId,ledger,authorityReader,supervisorReader,authorityPublic,supervisorPublic,clock=now}={}){
 if(!id(requestId)||typeof ledger?.inspect!=='function'||typeof authorityReader?.attest!=='function'||typeof supervisorReader?.attest!=='function'||!key(authorityPublic)||!key(supervisorPublic)||typeof clock!=='function')throw Error('RECOVERY_PORTS_REQUIRED');
 return Object.freeze({async inspect(){
  try{
   if(hex(await crypto.subtle.exportKey('raw',authorityPublic))===hex(await crypto.subtle.exportKey('raw',supervisorPublic)))return hold('ROLE_KEYS_NOT_DISTINCT');
   const before=await ledger.inspect();if(!ledgerValid(before,requestId))return hold('RESERVATION_NOT_ELIGIBLE');
   const b=base(requestId,crypto.randomUUID(),await digest(before));
   const s=await supervisorReader.attest(b),st=clock(),sb=s?.body;
   if(!sb||!fresh(sb.checked_at_epoch,st)||!exact(sb,{...b,role:'SUPERVISOR',runner_quiescent:true,pending_issue:false,checked_at_epoch:sb.checked_at_epoch})||!await verifyBody(supervisorPublic,sb,s.signature))return hold('QUIESCENCE_NOT_ESTABLISHED');
   const a=await authorityReader.attest(b),at=clock(),ab=a?.body;
   if(!ab||!fresh(ab.checked_at_epoch,at)||!fresh(sb.checked_at_epoch,at)||!exact(ab,{...b,role:'IAM',issuer_id:issuer,principal_id:principal,active:false,revoked:true,grant_sha256:ab.grant_sha256,issued_at_epoch:ab.issued_at_epoch,expires_at_epoch:ab.expires_at_epoch,checked_at_epoch:ab.checked_at_epoch})||!safe(ab.issued_at_epoch)||ab.issued_at_epoch<before.created||ab.issued_at_epoch>ab.checked_at_epoch||ab.expires_at_epoch-ab.issued_at_epoch!==120||typeof ab.grant_sha256!=='string'||!/^[0-9a-f]{64}$/.test(ab.grant_sha256)||!await verifyBody(authorityPublic,ab,a.signature))return hold('REVOCATION_NOT_ESTABLISHED');
   const after=await ledger.inspect(),end=clock();
   if(!ledgerValid(after,requestId)||await digest(after)!==b.ledger_sha256||!fresh(sb.checked_at_epoch,end)||!fresh(ab.checked_at_epoch,end))return hold('RESERVATION_OR_EVIDENCE_CHANGED');
   return {status:'TERMINAL_REVOCATION_OBSERVED',request_id:requestId,reservation_state:after.state,ledger_sha256:b.ledger_sha256,grant_sha256:ab.grant_sha256,verified_at_epoch:end,retry_allowed:false,promotion_allowed:false,receipt_pair_certified:false};
  }catch{return hold('INDEPENDENT_EVIDENCE_UNAVAILABLE');}
 }});
}
// No completion or release of the CP178 reservation is permitted by this result.
// The real supervisor port must independently establish quiescence and no pending
// issuance; a caller claim, timeout, signed fixture or expired grant is insufficient.

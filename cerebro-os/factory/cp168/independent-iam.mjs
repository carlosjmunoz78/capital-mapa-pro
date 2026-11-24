// Independent IAM authority boundary, LAB only. No production activation.
export const scope=Object.freeze({company_id:'fenix',engine_id:'FACT-001',environment:'LAB',capability:'FACT.INVENTORY.READ',read_only:true,external_mutation_allowed:false,cost_ceiling_eur:0});
export const issuer='iam:authority-lab-cp166',principal='iam:jarvis-cloud-lab-cp166',reader='iam:fact-cloud-lab-cp166';
const enc=new TextEncoder();
const err=x=>{throw Error(x)};
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{8,128}$/.test(x);
const time=()=>Math.floor(Date.now()/1000);
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const canonical=o=>enc.encode(JSON.stringify(o,Object.keys(o).sort()));
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const unhex=s=>Uint8Array.from(s.match(/../g),x=>parseInt(x,16));
const pub=k=>k?.type==='public'&&k.algorithm?.name==='Ed25519'&&k.usages.includes('verify');
const priv=k=>k?.type==='private'&&k.algorithm?.name==='Ed25519'&&k.usages.includes('sign');
export async function signBody(key,body){if(!priv(key))err('SIGNING_KEY_REQUIRED');return hex(await crypto.subtle.sign('Ed25519',key,canonical(body)));}
export async function verifyBody(key,body,sig){if(!pub(key)||typeof sig!=='string'||!/^[0-9a-f]{128}$/.test(sig))return false;return crypto.subtle.verify('Ed25519',key,unhex(sig),canonical(body));}
export function command(action,requestId,nonce,t=time()){
 if(!['issue','current','revoke'].includes(action)||!id(requestId)||!id(nonce)||!Number.isSafeInteger(t))err('COMMAND_INVALID');
 return {...scope,action,request_id:requestId,nonce,version:'1.0.0',principal_id:principal,actor_id:action==='current'?reader:principal,emitted_at_epoch:t};
}
function fresh(c,t){return Number.isSafeInteger(c?.emitted_at_epoch)&&c.emitted_at_epoch<=t&&t-c.emitted_at_epoch<=30;}
const ref=x=>'policy://cp166/'+x;
function validateCommand(c,action,t){if(!fresh(c,t)||!id(c?.request_id)||!id(c?.nonce)||!exact(c,command(action,c.request_id,c.nonce,c.emitted_at_epoch)))err('COMMAND_SCOPE_DENIED');}
function grant(c,t){return {...scope,issuer_id:issuer,principal_id:principal,request_id:c.request_id,policy_receipt_ref:ref(c.request_id),version:'1.0.0',decision:'ALLOW_READ_ONLY',active:true,revoked:false,issued_at_epoch:t,expires_at_epoch:t+120};}
export function createIndependentAuthority({enabled=false,principalKey,readerKey,signingKey,store,clock=time}={}){
 if(enabled!==true||!pub(principalKey)||!pub(readerKey)||!priv(signingKey)||!store||typeof store.transition!=='function'||typeof clock!=='function')err('AUTHORITY_CONFIGURATION_DENIED');
 // Reject reused actor/authority keys before any persistent state transition.
 async function auth(c,sig,action,key){const t=clock();validateCommand(c,action,t);const j=hex(await crypto.subtle.exportKey('raw',principalKey)),f=hex(await crypto.subtle.exportKey('raw',readerKey));if(j===f)err('KEY_SEPARATION_DENIED');const probe={domain:'CP166_KEY_SEPARATION_ONLY',nonce:crypto.randomUUID()};const proof=await signBody(signingKey,probe);if(await verifyBody(principalKey,probe,proof)||await verifyBody(readerKey,probe,proof))err('KEY_SEPARATION_DENIED');if(!await verifyBody(key,c,sig))err('ACTOR_SIGNATURE_DENIED');const t2=clock();validateCommand(c,action,t2);return t2;}
 return Object.freeze({
  async issue(c,sig){const t=await auth(c,sig,'issue',principalKey);const g=grant(c,t);store.transition('issue',c.request_id,c.nonce,g,t);return {policy_receipt_ref:g.policy_receipt_ref,expires_at_epoch:g.expires_at_epoch};},
  async current(c,sig){const t=await auth(c,sig,'current',readerKey);const g=store.transition('current',c.request_id,c.nonce,null,t);if(!g||g.active!==true||g.revoked!==false||g.expires_at_epoch<=t)err('GRANT_INACTIVE');const body={...g,checked_at_epoch:t,reader_nonce:c.nonce};return {body,signature:await signBody(signingKey,body)};},
  async revoke(c,sig){const t=await auth(c,sig,'revoke',principalKey);store.transition('revoke',c.request_id,c.nonce,null,t);return {state:'REVOKED'};}
 });
}
export async function verifyCurrentGrant({envelope,authorityPublicKey,requestId,readerNonce,now=time()}={}){
 const b=envelope?.body;if(!id(requestId)||!id(readerNonce)||!Number.isSafeInteger(now)||!b||!await verifyBody(authorityPublicKey,b,envelope.signature))err('AUTHORITY_SIGNATURE_DENIED');
 const expected={...scope,issuer_id:issuer,principal_id:principal,request_id:requestId,policy_receipt_ref:ref(requestId),version:'1.0.0',decision:'ALLOW_READ_ONLY',active:true,revoked:false,issued_at_epoch:b.issued_at_epoch,expires_at_epoch:b.expires_at_epoch,checked_at_epoch:b.checked_at_epoch,reader_nonce:readerNonce};
 if(!exact(b,expected)||![b.issued_at_epoch,b.expires_at_epoch,b.checked_at_epoch].every(Number.isSafeInteger)||!(0<=b.issued_at_epoch&&b.issued_at_epoch<=b.checked_at_epoch&&b.checked_at_epoch<=now&&now<b.expires_at_epoch&&b.expires_at_epoch-b.issued_at_epoch===120&&now-b.checked_at_epoch<=10))err('AUTHORITY_STATE_DENIED');
 const {reader_nonce,...g}=b;return Object.freeze({...g,verified:true});
}

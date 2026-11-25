export const principal='iam:jarvis-cloud-lab-cp164',issuer='iam:fact-lab-authority-cp164',id='CP164-JARVIS-CANARY-001',ref='policy://cp164/'+id;
export const scope=Object.freeze({company_id:'fenix',engine_id:'FACT-001',environment:'LAB',capability:'FACT.INVENTORY.READ',read_only:true,external_mutation_allowed:false,cost_ceiling_eur:0});
export const now=()=>Math.floor(Date.now()/1000);
export const canonical=o=>JSON.stringify(o,Object.keys(o).sort());
const enc=new TextEncoder();
const hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const bytes=s=>Uint8Array.from(s.match(/../g),x=>parseInt(x,16));
const key=async s=>{if(typeof s!=='string'||!/^[0-9a-f]{64}$/.test(s))throw Error('KEY_REQUIRED');return crypto.subtle.importKey('raw',bytes(s),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);};
export async function sign(s,o){return hex(await crypto.subtle.sign('HMAC',await key(s),enc.encode(canonical(o))));}
export async function verify(s,o,sig){if(typeof sig!=='string'||!/^[0-9a-f]{64}$/.test(sig))return false;return crypto.subtle.verify('HMAC',await key(s),bytes(sig),enc.encode(canonical(o)));}
export const request=(t=now())=>({...scope,request_id:id,version:'1.0.0',principal_id:principal,policy_receipt_ref:ref,emitted_at_epoch:t});
export const control=(action,t=now())=>({action,company_id:'fenix',environment:'LAB',principal_id:principal,request_id:id,emitted_at_epoch:t});
export function exact(o,expected,t=now()){return o&&typeof o==='object'&&!Array.isArray(o)&&Object.keys(o).sort().join('|')===Object.keys(expected).sort().join('|')&&Object.entries(expected).every(([k,v])=>k==='emitted_at_epoch'||o[k]===v)&&Number.isSafeInteger(o.emitted_at_epoch)&&o.emitted_at_epoch<=t&&t-o.emitted_at_epoch<=60;}
export function makeGrant(r,t=now()){if(!exact(r,request(t),t))throw Error('SCOPE_DENIED');return {...scope,request_id:id,version:'1.0.0',principal_id:principal,policy_receipt_ref:ref,issuer_id:issuer,decision:'ALLOW_READ_ONLY',verified:true,active:true,revoked:false,issued_at_epoch:r.emitted_at_epoch,expires_at_epoch:r.emitted_at_epoch+120,checked_at_epoch:t};}
export function current(g,t=now()){if(!g||g.revoked||!g.active||g.expires_at_epoch<=t||g.issued_at_epoch>t)throw Error('GRANT_INACTIVE');return {...g,checked_at_epoch:t};}
export function revoked(g,t=now()){return {...g,active:false,revoked:true,checked_at_epoch:t};}
export async function hash(o){return hex(await crypto.subtle.digest('SHA-256',enc.encode(JSON.stringify(o))));}

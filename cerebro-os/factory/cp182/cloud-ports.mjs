// CP182: private cloud entrypoints. Only the fixed LAB canary is permitted.
import {DurableObject,WorkerEntrypoint,WorkflowEntrypoint} from 'cloudflare:workers';
import {cp180RequestId as id,createBoundedStore} from '../cp169/bounded-store.mjs';
import {createIndependentAuthority,signBody,verifyBody,scope,issuer,principal} from '../cp169/independent-iam.mjs';
import {decode,publicKey,privateKey} from '../cp169/key-import.mjs';
import {importReceiptKey} from '../cp176/receipt-ports.mjs';
import {rpcBody,createReceiptStore,createPrivateFactPort,createPrivateTribunalPort,createPrivateJarvisPort,createJarvisStorage} from '../cp181/private-ports.mjs';
const fail=m=>{throw Error(m)},now=()=>Math.floor(Date.now()/1000),enc=new TextEncoder();
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const digest=async b=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(JSON.stringify(b,Object.keys(b).sort())))),x=>x.toString(16).padStart(2,'0')).join('');
const fresh=(t,n=now())=>Number.isSafeInteger(t)&&t<=n&&t>=0&&n-t<=30;
const mac=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const enable=e=>{if(e.CP182_ENABLED!=='true')fail('CP182_DISABLED');};
const keyset=async e=>({jarvisPublic:await publicKey(e.JARVIS_PUBLIC),factPublic:await publicKey(e.FACT_PUBLIC),authorityPublic:await publicKey(e.AUTHORITY_PUBLIC),tribunalPublic:await publicKey(e.TRIBUNAL_PUBLIC)});
const verifyKey=async s=>{const b=decode(s);if(b.length!==32)fail('MAC_KEY_LENGTH');return crypto.subtle.importKey('raw',b,{name:'HMAC',hash:'SHA-256'},false,['verify']);};
const signKey=s=>importReceiptKey(decode(s));
async function inspectAuth(e,q,sig){enable(e);if(!fresh(q?.emitted_at_epoch)||!exact(q,rpcBody('inspect',q?.nonce,q?.emitted_at_epoch))||!await verifyBody(await publicKey(e.INGRESS_PUBLIC),q,sig)||!fresh(q.emitted_at_epoch))fail('CP182_INSPECT_DENIED');}
const ledger=(e,name)=>{enable(e);if(!e.LEDGER)fail('LEDGER_REQUIRED');const ns=e.LEDGER.jurisdiction('eu');return ns.get(ns.idFromName(name));};
const err404=()=>new Response(null,{status:404,headers:{'cache-control':'no-store'}});
export const closed={fetch:err404};
export class AuthorityLedger182 extends DurableObject{
 constructor(ctx,env){super(ctx,env);this.storage=ctx.storage;this.e=env;}
 async #run(action,c,sig){enable(this.e);if(c?.request_id!==id)fail('CANARY_SCOPE_DENIED');const e=this.e;const [j,f,a]=await Promise.all([publicKey(e.JARVIS_PUBLIC),publicKey(e.FACT_PUBLIC),privateKey(e.AUTHORITY_PRIVATE)]);return createIndependentAuthority({enabled:true,principalKey:j,readerKey:f,signingKey:a,store:createBoundedStore(this.storage,{canaryId:id})})[action](c,sig);}
 issue(c,s){return this.#run('issue',c,s)} current(c,s){return this.#run('current',c,s)} revoke(c,s){return this.#run('revoke',c,s)}
 async observe(q,s){await inspectAuth(this.e,q,s);createBoundedStore(this.storage,{canaryId:id});const rows=this.storage.sql.exec('SELECT body FROM cp168_grant WHERE id=?',id).toArray();if(rows.length!==1)fail('GRANT_ABSENT');const g=JSON.parse(rows[0].body);if(!exact(g,{...scope,issuer_id:issuer,principal_id:principal,request_id:id,policy_receipt_ref:'policy://cp166/'+id,version:'1.0.0',decision:'ALLOW_READ_ONLY',active:false,revoked:true,issued_at_epoch:g.issued_at_epoch,expires_at_epoch:g.expires_at_epoch})||!Number.isSafeInteger(g.issued_at_epoch)||g.expires_at_epoch-g.issued_at_epoch!==120||g.issued_at_epoch>now())fail('REVOCATION_NOT_ESTABLISHED');
 const body={...scope,request_id:id,role:'IAM',nonce:q.nonce,active:false,revoked:true,grant_sha256:await digest(g),checked_at_epoch:now()};return {body,signature:await signBody(await privateKey(this.e.AUTHORITY_PRIVATE),body)};}
}
export class Authority182 extends WorkerEntrypoint{
 issue(c,s){return ledger(this.env,'cp182-authority').issue(c,s)} current(c,s){return ledger(this.env,'cp182-authority').current(c,s)} revoke(c,s){return ledger(this.env,'cp182-authority').revoke(c,s)} observe(c,s){return ledger(this.env,'cp182-authority').observe(c,s)}
}
export class FactLedger182 extends DurableObject{
 constructor(ctx,env){super(ctx,env);this.storage=ctx.storage;this.e=env;}
 async #port(){const e=this.e;enable(e);return createPrivateFactPort({...await keyset(e),db:e.RECOVERY_DB,iam:e.IAM,factPrivate:await privateKey(e.FACT_PRIVATE),receiptKey:await signKey(e.FACT_MAC),store:createReceiptStore(this.storage,'FACT-001')});}
 async read(q,s){return (await this.#port()).read(q,s)} async current(q,s){return (await this.#port()).current(q,s)} async persisted(q,s){return (await this.#port()).persisted(q,s)}
}
export class Fact182 extends WorkerEntrypoint{
 read(q,s){return ledger(this.env,'cp182-fact').read(q,s)} current(q,s){return ledger(this.env,'cp182-fact').current(q,s)} persisted(q,s){return ledger(this.env,'cp182-fact').persisted(q,s)}
}
export class TribunalLedger182 extends DurableObject{
 constructor(ctx,env){super(ctx,env);this.storage=ctx.storage;this.e=env;this.sql=ctx.storage.sql;this.sql.exec('CREATE TABLE IF NOT EXISTS cp182_verdict (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');}
 #get(){const r=this.sql.exec('SELECT payload FROM cp182_verdict WHERE id=?',id).toArray();return r.length===1?JSON.parse(r[0].payload):null;}
 async verify(j,f,q,s){const e=this.e;enable(e);if(this.#get())fail('VERDICT_ALREADY_PERSISTED');const keys=await keyset(e),priv=await privateKey(e.TRIBUNAL_PRIVATE);const p=await createPrivateTribunalPort({...keys,tribunalPrivate:priv,jarvisVerifyKey:await verifyKey(e.JARVIS_MAC),factVerifyKey:await verifyKey(e.FACT_MAC),fact:e.FACT});const r=await p.verify(j,f,q,s);const body={...scope,request_id:id,role:'TRIBUNAL',status:r.status,iam_grant_verified:r.iam_grant_verified,promotion_allowed:false,jarvis_mac:j.mac,fact_mac:f.mac,result_sha256:f.body.result_sha256,checked_at_epoch:now()};const proof={body,signature:await signBody(priv,body)};
 this.storage.transactionSync(()=>{if(this.#get())fail('VERDICT_ALREADY_PERSISTED');this.sql.exec('INSERT INTO cp182_verdict VALUES (?,?)',id,JSON.stringify(proof));});return r;}
 async inspect(q,s){await inspectAuth(this.e,q,s);const proof=this.#get();if(!proof)fail('VERDICT_NOT_PERSISTED');const c=rpcBody('persisted',crypto.randomUUID(),now());const f=await this.e.FACT.persisted(c,await signBody(await privateKey(this.e.TRIBUNAL_PRIVATE),c));if(!f||f.mac!==proof.body.fact_mac||f.body?.result_sha256!==proof.body.result_sha256)fail('FACT_READBACK_DENIED');return {proof,fact:f};}
}
export class Tribunal182 extends WorkerEntrypoint{
 verify(j,f,q,s){return ledger(this.env,'cp182-tribunal').verify(j,f,q,s)} inspect(q,s){return ledger(this.env,'cp182-tribunal').inspect(q,s)}
}
export class JarvisLedger182 extends DurableObject{
 constructor(ctx,env){super(ctx,env);this.storage=ctx.storage;this.e=env;}
 async #port(){const e=this.e;enable(e);return createPrivateJarvisPort({...await keyset(e),...createJarvisStorage(this.storage),ingressPublic:await publicKey(e.INGRESS_PUBLIC),jarvisPrivate:await privateKey(e.JARVIS_PRIVATE),receiptKey:await signKey(e.JARVIS_MAC),iam:e.IAM,fact:e.FACT,tribunal:e.TRIBUNAL});}
 async run(q,s){return (await this.#port()).run(q,s)} async inspect(q,s){return (await this.#port()).inspect(q,s)}
}
export const instanceId='cp182-private-pair-001';
export async function executePair(e,p){
 enable(e);const ingress=await publicKey(e.INGRESS_PUBLIC);
 if(!p||Object.keys(p).sort().join('|')!=='inspect|inspect_signature|run|run_signature'||!fresh(p.run?.emitted_at_epoch)||!exact(p.run,rpcBody('run',p.run?.nonce,p.run?.emitted_at_epoch))||!await verifyBody(ingress,p.run,p.run_signature))fail('WORKFLOW_INGRESS_DENIED');
 await inspectAuth(e,p.inspect,p.inspect_signature);
 const j=ledger(e,'cp182-jarvis');const out=await j.run(p.run,p.run_signature);
 if(out?.status!=='CP178_ONE_SHOT_COMPLETED'||out.request_id!==id||out.grant_revoked!==true||out.promotion_allowed!==false)fail('ONE_SHOT_RESULT_DENIED');
 const [state,authority,tribunal]=await Promise.all([j.inspect(p.inspect,p.inspect_signature),e.IAM.observe(p.inspect,p.inspect_signature),e.TRIBUNAL.inspect(p.inspect,p.inspect_signature)]);
 const ab=authority?.body,tb=tribunal?.proof?.body,jr=state?.receipt,fr=tribunal?.fact;
 if(state?.reservation?.state!=='COMPLETED'||state.reservation.request_id!==id||!jr||!fr||!mac(jr.mac)||!mac(fr.mac)||!ab||!tb||!fresh(ab.checked_at_epoch)||!fresh(tb.checked_at_epoch)||!exact(ab,{...scope,request_id:id,role:'IAM',nonce:p.inspect.nonce,active:false,revoked:true,grant_sha256:ab.grant_sha256,checked_at_epoch:ab.checked_at_epoch})||!mac(ab.grant_sha256)||!await verifyBody(await publicKey(e.AUTHORITY_PUBLIC),ab,authority.signature)||!exact(tb,{...scope,request_id:id,role:'TRIBUNAL',status:'VERIFIED_AUTHORIZED_PAIR',iam_grant_verified:true,promotion_allowed:false,jarvis_mac:jr.mac,fact_mac:fr.mac,result_sha256:fr.body.result_sha256,checked_at_epoch:tb.checked_at_epoch})||!mac(tb.result_sha256)||!await verifyBody(await publicKey(e.TRIBUNAL_PUBLIC),tb,tribunal.proof.signature))fail('INDEPENDENT_READBACK_DENIED');
 let duplicate=false;try{await j.run(p.run,p.run_signature);}catch(x){duplicate=String(x.message).includes('ALREADY_RESERVED_NO_RETRY');}if(!duplicate)fail('REPLAY_NOT_ESTABLISHED');
 return {status:'CP182_CLOUD_PAIR_VERIFIED',request_id:id,company_id:'fenix',environment:'LAB',reservation:'COMPLETED',grant_revoked:true,duplicate_denied:true,jarvis_receipt_sha256:await digest(jr.body),fact_receipt_sha256:await digest(fr.body),grant_sha256:ab.grant_sha256,result_sha256:tb.result_sha256,tribunal_signature_verified:true,promotion_allowed:false};
}
export class PairWorkflow182 extends WorkflowEntrypoint{
 async run(event,step){if(event.instanceId!==instanceId)fail('WORKFLOW_INSTANCE_DENIED');return step.do('one signed private pair',{retries:{limit:0,delay:'1 second'},timeout:'45 seconds'},()=>executePair(this.env,event.payload));}
}

// Reusable bounded LAB gateway; original CP182 workflow/ledgers remain isolated.
import {WorkerEntrypoint} from 'cloudflare:workers';
import {AuthorityLedger182 as OldIAM,FactLedger182 as OldFACT,TribunalLedger182 as OldTribunal,JarvisLedger182 as OldJarvis,PairWorkflow182 as OldWorkflow,PairAuditWorkflow182,closed} from '../factory/cp182/cloud-ports.mjs';
import {createBoundedStore,cp180RequestId} from '../factory/cp169/bounded-store.mjs';
import {createIndependentAuthority,signBody,verifyBody,scope,issuer,principal} from '../factory/cp169/independent-iam.mjs';
import {decode,publicKey,privateKey} from '../factory/cp169/key-import.mjs';
import {importReceiptKey} from '../factory/cp176/receipt-ports.mjs';
import {coreId,rpcBody,createReceiptStore,createPrivateFactPort,createPrivateTribunalPort,createPrivateJarvisPort,createJarvisStorage} from './core-ports.mjs';
export {PairAuditWorkflow182,closed};
const fail=s=>{throw Error(s)},now=()=>Math.floor(Date.now()/1000),enc=new TextEncoder();
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const hash=async x=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(JSON.stringify(x)))),v=>v.toString(16).padStart(2,'0')).join('');
const bodyHash=x=>hash(Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])));
const fresh=t=>Number.isSafeInteger(t)&&t<=now()&&now()-t<=30;
const enable=e=>{if(e.CORE_ENABLED!=='true'||e.CP182_ENABLED!=='true')fail('CORE_DISABLED');};
const keys=async e=>({jarvisPublic:await publicKey(e.JARVIS_PUBLIC),factPublic:await publicKey(e.FACT_PUBLIC),authorityPublic:await publicKey(e.AUTHORITY_PUBLIC),tribunalPublic:await publicKey(e.TRIBUNAL_PUBLIC)});
const vk=async s=>crypto.subtle.importKey('raw',decode(s),{name:'HMAC',hash:'SHA-256'},false,['verify']);
const sk=s=>importReceiptKey(decode(s));
const stub=(e,role,id)=>{enable(e);coreId(id);const ns=e.LEDGER.jurisdiction('eu');return ns.get(ns.idFromName('core-lab-'+role+'-'+id));};
const historic=(q)=>q?.request_id===cp180RequestId;
async function inspectAuth(e,q,s){enable(e);coreId(q?.request_id);if(!fresh(q.emitted_at_epoch)||!exact(q,rpcBody(q.request_id,'inspect',q.nonce,q.emitted_at_epoch))||!await verifyBody(await publicKey(e.CORE_INGRESS_PUBLIC),q,s))fail('CORE_INSPECT_DENIED');}
export class AuthorityLedger182 extends OldIAM{
 async core(action,q,s){enable(this.e);const id=coreId(q?.request_id),e=this.e;const [j,f,a]=await Promise.all([publicKey(e.JARVIS_PUBLIC),publicKey(e.FACT_PUBLIC),privateKey(e.AUTHORITY_PRIVATE)]);return createIndependentAuthority({enabled:true,principalKey:j,readerKey:f,signingKey:a,store:createBoundedStore(this.storage,{canaryId:id})})[action](q,s);}
 issue(q,s){return historic(q)?super.issue(q,s):this.core('issue',q,s)}
 current(q,s){return historic(q)?super.current(q,s):this.core('current',q,s)}
 revoke(q,s){return historic(q)?super.revoke(q,s):this.core('revoke',q,s)}
 async observe(q,s){if(historic(q))return super.observe(q,s);await inspectAuth(this.e,q,s);const id=q.request_id,rows=this.storage.sql.exec('SELECT body FROM cp168_grant WHERE id=?',id).toArray();if(rows.length!==1)fail('GRANT_ABSENT');const g=JSON.parse(rows[0].body);if(!exact(g,{...scope,issuer_id:issuer,principal_id:principal,request_id:id,policy_receipt_ref:'policy://cp166/'+id,version:'1.0.0',decision:'ALLOW_READ_ONLY',active:false,revoked:true,issued_at_epoch:g.issued_at_epoch,expires_at_epoch:g.expires_at_epoch}))fail('CORE_GRANT_NOT_REVOKED');const body={...scope,request_id:id,role:'IAM',nonce:q.nonce,active:false,revoked:true,grant_sha256:await bodyHash(g),checked_at_epoch:now()};return {body,signature:await signBody(await privateKey(this.e.AUTHORITY_PRIVATE),body)};}
}
function roleStub(e,role,q){if(historic(q)){const ns=e.LEDGER.jurisdiction('eu');return ns.get(ns.idFromName('cp182-'+role));}return stub(e,role,q?.request_id);}
export class Authority182 extends WorkerEntrypoint{
 issue(q,s){return roleStub(this.env,'authority',q).issue(q,s)} current(q,s){return roleStub(this.env,'authority',q).current(q,s)} revoke(q,s){return roleStub(this.env,'authority',q).revoke(q,s)} observe(q,s){return roleStub(this.env,'authority',q).observe(q,s)} audit(q,s){if(!historic(q))fail('HISTORIC_ONLY');return roleStub(this.env,'authority',q).audit(q,s)}
}
export class FactLedger182 extends OldFACT{
 async port(id){enable(this.e);coreId(id);const e=this.e;return createPrivateFactPort({...await keys(e),canaryId:id,db:e.RECOVERY_DB,iam:e.IAM,factPrivate:await privateKey(e.FACT_PRIVATE),receiptKey:await sk(e.FACT_MAC),store:createReceiptStore(this.storage,'FACT-001',id)});}
 async read(q,s){return historic(q)?super.read(q,s):(await this.port(q?.request_id)).read(q,s)} async current(q,s){return historic(q)?super.current(q,s):(await this.port(q?.request_id)).current(q,s)} async persisted(q,s){return historic(q)?super.persisted(q,s):(await this.port(q?.request_id)).persisted(q,s)}
}
export class Fact182 extends WorkerEntrypoint{
 read(q,s){return roleStub(this.env,'fact',q).read(q,s)} current(q,s){return roleStub(this.env,'fact',q).current(q,s)} persisted(q,s){return roleStub(this.env,'fact',q).persisted(q,s)} audit(q,s){if(!historic(q))fail('HISTORIC_ONLY');return roleStub(this.env,'fact',q).audit(q,s)}
}
export class TribunalLedger182 extends OldTribunal{
 get(id){const r=this.storage.sql.exec('SELECT payload FROM cp182_verdict WHERE id=?',id).toArray();return r.length===1?JSON.parse(r[0].payload):null;}
 async verify(j,f,q,s){if(historic(q))return super.verify(j,f,q,s);enable(this.e);const id=coreId(q?.request_id),e=this.e;if(this.get(id))fail('VERDICT_ALREADY_PERSISTED');const priv=await privateKey(e.TRIBUNAL_PRIVATE);const p=await createPrivateTribunalPort({...await keys(e),canaryId:id,tribunalPrivate:priv,jarvisVerifyKey:await vk(e.JARVIS_MAC),factVerifyKey:await vk(e.FACT_MAC),fact:e.FACT});const r=await p.verify(j,f,q,s);const body={...scope,request_id:id,role:'TRIBUNAL',status:r.status,iam_grant_verified:r.iam_grant_verified,promotion_allowed:false,jarvis_mac:j.mac,fact_mac:f.mac,result_sha256:f.body.result_sha256,checked_at_epoch:now()};const proof={body,signature:await signBody(priv,body)};this.storage.transactionSync(()=>{if(this.get(id))fail('VERDICT_ALREADY_PERSISTED');this.storage.sql.exec('INSERT INTO cp182_verdict VALUES (?,?)',id,JSON.stringify(proof));});return r;}
 async inspect(q,s){if(historic(q))return super.inspect(q,s);await inspectAuth(this.e,q,s);const id=q.request_id,proof=this.get(id);if(!proof)fail('VERDICT_NOT_PERSISTED');const c=rpcBody(id,'persisted',crypto.randomUUID(),now()),f=await this.e.FACT.persisted(c,await signBody(await privateKey(this.e.TRIBUNAL_PRIVATE),c));if(!f||f.mac!==proof.body.fact_mac||f.body.result_sha256!==proof.body.result_sha256)fail('FACT_READBACK_DENIED');return {proof,fact:f};}
}
export class Tribunal182 extends WorkerEntrypoint{
 verify(j,f,q,s){return roleStub(this.env,'tribunal',q).verify(j,f,q,s)} inspect(q,s){return roleStub(this.env,'tribunal',q).inspect(q,s)} audit(q,s){if(!historic(q))fail('HISTORIC_ONLY');return roleStub(this.env,'tribunal',q).audit(q,s)}
}
export class JarvisLedger182 extends OldJarvis{
 async port(id){enable(this.e);coreId(id);const e=this.e;return createPrivateJarvisPort({...await keys(e),...createJarvisStorage(this.storage,id),canaryId:id,ingressPublic:await publicKey(e.CORE_INGRESS_PUBLIC),jarvisPrivate:await privateKey(e.JARVIS_PRIVATE),receiptKey:await sk(e.JARVIS_MAC),iam:e.IAM,fact:e.FACT,tribunal:e.TRIBUNAL});}
 async run(q,s){return historic(q)?super.run(q,s):(await this.port(q?.request_id)).run(q,s)} async inspect(q,s){return historic(q)?super.inspect(q,s):(await this.port(q?.request_id)).inspect(q,s)}
}
export function routeOrder(p,instance){if(typeof p==='string'){if(p.length>2048)fail('CORE_PAYLOAD_DENIED');p=JSON.parse(p);}const id=coreId(p?.request_id);const route={company_id:'fenix',engine_id:'FACT-001',environment:'LAB',version:'1.0.0',capability:'FACT.INVENTORY.READ',request_id:id};if(!exact(p,route)||instance!==id.toLowerCase())fail('CORE_ROUTE_DENIED');return route;}
export async function executeOrder(e,p,instance){enable(e);const route=routeOrder(p,instance),id=route.request_id,priv=await privateKey(e.CORE_INGRESS_PRIVATE),pub=await publicKey(e.CORE_INGRESS_PUBLIC);
 const q=rpcBody(id,'run',crypto.randomUUID(),now()),sig=await signBody(priv,q);if(!await verifyBody(pub,q,sig))fail('GATEWAY_KEY_MISMATCH');const j=stub(e,'jarvis',id),out=await j.run(q,sig);
 if(out?.status!=='CP178_ONE_SHOT_COMPLETED'||out.request_id!==id||out.grant_revoked!==true||out.promotion_allowed!==false||out.result?.request_id!==id)fail('CORE_EXECUTION_DENIED');
 const inspect=rpcBody(id,'inspect',crypto.randomUUID(),now()),is=await signBody(priv,inspect);const [state,a,t]=await Promise.all([j.inspect(inspect,is),e.IAM.observe(inspect,is),e.TRIBUNAL.inspect(inspect,is)]);
 const ab=a?.body,tb=t?.proof?.body,jr=state?.receipt,fr=t?.fact,h=await hash(out.result);
 if(state?.reservation?.state!=='COMPLETED'||state.reservation.request_id!==id||!jr||!fr||!fresh(ab?.checked_at_epoch)||!fresh(tb?.checked_at_epoch)||!exact(ab,{...scope,request_id:id,role:'IAM',nonce:inspect.nonce,active:false,revoked:true,grant_sha256:ab.grant_sha256,checked_at_epoch:ab.checked_at_epoch})||!await verifyBody(await publicKey(e.AUTHORITY_PUBLIC),ab,a.signature)||!exact(tb,{...scope,request_id:id,role:'TRIBUNAL',status:'VERIFIED_AUTHORIZED_PAIR',iam_grant_verified:true,promotion_allowed:false,jarvis_mac:jr.mac,fact_mac:fr.mac,result_sha256:h,checked_at_epoch:tb.checked_at_epoch})||fr.body.result_sha256!==h||!await verifyBody(await publicKey(e.TRIBUNAL_PUBLIC),tb,t.proof.signature))fail('CORE_SUPERVISION_HOLD');
 return {status:'CORE_ORDER_COMPLETED',route,result:out.result,supervision:'TERMINAL_REVOKED_VERIFIED',grant_revoked:true,tribunal_verified:true,receipt_hashes:{jarvis:await bodyHash(jr.body),fact:await bodyHash(fr.body),grant:ab.grant_sha256,result:h},promotion_allowed:false};
}
export class PairWorkflow182 extends OldWorkflow{
 async run(event,step){if(!event.instanceId.startsWith('core-order-'))return super.run(event,step);routeOrder(event.payload,event.instanceId);return step.do('gateway to JARVIS IAM FACT Tribunal', {retries:{limit:0,delay:'1 second'},timeout:'45 seconds'},()=>executeOrder(this.env,event.payload,event.instanceId));}
}

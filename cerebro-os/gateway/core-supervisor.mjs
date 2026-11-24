// Read-only independent supervisor over terminal cloud orders; no issue/read-inventory/retry.
import {signBody,verifyBody,scope,principal} from '../factory/cp169/independent-iam.mjs';
import {publicKey,privateKey} from '../factory/cp169/key-import.mjs';
import {coreId,rpcBody} from './core-ports.mjs';
import {cp131Scope} from '../factory/cp176/receipt-ports.mjs';
const fail=s=>{throw Error(s)},clock=()=>Math.floor(Date.now()/1000),enc=new TextEncoder(),hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const digest=async x=>hex(await crypto.subtle.digest('SHA-256',enc.encode(JSON.stringify(x))));
const bodyHash=x=>digest(Object.fromEntries(Object.keys(x).sort().map(k=>[k,x[k]])));
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const mac=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const safe=x=>Number.isSafeInteger(x)&&x>=0;
const fresh=(t,n)=>safe(t)&&t<=n&&n-t<=30;
export async function superviseCompletedOrder(e,id,{now=clock}={}){
 if(e.CORE_SUPERVISOR_ENABLED!=='true')fail('SUPERVISOR_DISABLED');
 coreId(id);
 if(!e.CORE_WORKFLOW||typeof e.IAM?.observe!=='function'||typeof e.TRIBUNAL?.inspect!=='function')fail('SUPERVISOR_PORTS_REQUIRED');
 const roleKeys=[e.CORE_SUPERVISOR_PUBLIC,e.AUTHORITY_PUBLIC,e.TRIBUNAL_PUBLIC,e.CORE_INGRESS_PUBLIC,e.JARVIS_PUBLIC,e.FACT_PUBLIC];if(new Set(roleKeys).size!==6||roleKeys.some(k=>typeof k!=='string'))fail('SUPERVISOR_KEY_COLLISION');
 const priv=await privateKey(e.CORE_SUPERVISOR_PRIVATE),pub=await publicKey(e.CORE_SUPERVISOR_PUBLIC);
 const instance=await e.CORE_WORKFLOW.get(id.toLowerCase()),s=await instance.status(),o=s?.output,r=o?.result,hashes=o?.receipt_hashes;
 if(s?.status!=='complete'||s.error||o?.status!=='CORE_ORDER_COMPLETED'||!exact(o.route,{company_id:'fenix',engine_id:'FACT-001',environment:'LAB',version:'1.0.0',capability:'FACT.INVENTORY.READ',request_id:id})||r?.request_id!==id||r.company_id!=='fenix'||r.environment!=='LAB'||r.engine_id!=='FACT-001'||r.status!=='CANDIDATE_INVENTORY_READ'||r.external_mutation_allowed!==false||r.promotion_allowed!==false||o.grant_revoked!==true||o.tribunal_verified!==true||o.promotion_allowed!==false||!hashes||Object.keys(hashes).sort().join('|')!=='fact|grant|jarvis|result'||!Object.values(hashes).every(mac))fail('TERMINAL_PROVIDER_EVIDENCE_DENIED');
 const h=await digest(r);if(h!==hashes.result)fail('RESULT_HASH_DENIED');
 const q=rpcBody(id,'inspect',crypto.randomUUID(),now()),sig=await signBody(priv,q);if(!await verifyBody(pub,q,sig))fail('SUPERVISOR_KEY_MISMATCH');
 if(e.CORE_JARVIS_DIRECT_REQUIRED!=='true'||!e.JARVIS_LEDGER||typeof e.JARVIS_LEDGER.jurisdiction!=='function')fail('JARVIS_DIRECT_PORT_REQUIRED');
 const jns=e.JARVIS_LEDGER.jurisdiction('eu'),js=jns.get(jns.idFromName('core-lab-jarvis-'+id));const [a,t,j]=await Promise.all([e.IAM.observe(q,sig),e.TRIBUNAL.inspect(q,sig),js.inspect(q,sig)]),ab=a?.body,tb=t?.proof?.body,fr=t?.fact,jb=j?.body,at=now();
 if(!ab||!fresh(ab.checked_at_epoch,at)||!exact(ab,{...scope,request_id:id,role:'IAM',nonce:q.nonce,active:false,revoked:true,grant_sha256:hashes.grant,checked_at_epoch:ab.checked_at_epoch})||!await verifyBody(await publicKey(e.AUTHORITY_PUBLIC),ab,a.signature))fail('INDEPENDENT_IAM_DENIED');
 if(!tb||!safe(tb.checked_at_epoch)||tb.checked_at_epoch>at||!mac(tb.jarvis_mac)||!mac(tb.fact_mac)||!fr||!exact(tb,{...scope,request_id:id,role:'TRIBUNAL',status:'VERIFIED_AUTHORIZED_PAIR',iam_grant_verified:true,promotion_allowed:false,jarvis_mac:tb.jarvis_mac,fact_mac:fr.mac,result_sha256:h,checked_at_epoch:tb.checked_at_epoch})||!await verifyBody(await publicKey(e.TRIBUNAL_PUBLIC),tb,t.proof.signature))fail('INDEPENDENT_TRIBUNAL_DENIED');
 if(!safe(fr.body?.emitted_at_epoch)||fr.body.emitted_at_epoch>tb.checked_at_epoch||!exact(fr.body,{...cp131Scope,request_id:id,principal_id:principal,policy_receipt_ref:'policy://cp166/'+id,emitted_at_epoch:fr.body.emitted_at_epoch,origin:'FACT-001',target:'JARVIS',status:'COMPLETED',result_sha256:h})||await bodyHash(fr.body)!==hashes.fact)fail('FACT_PERSISTENCE_DENIED');
 if(!jb||!fresh(jb.checked_at_epoch,at)||!exact(jb,{...scope,request_id:id,role:'JARVIS',nonce:q.nonce,reservation_state:'COMPLETED',jarvis_mac:tb.jarvis_mac,jarvis_sha256:hashes.jarvis,checked_at_epoch:jb.checked_at_epoch})||!await verifyBody(await publicKey(e.JARVIS_PUBLIC),jb,j.signature))fail('INDEPENDENT_JARVIS_DENIED');
 const again=await instance.status();if(again.status!=='complete'||again.error||await digest(again.output)!==await digest(o)||(!fresh(ab.checked_at_epoch,now())||!fresh(jb.checked_at_epoch,now())))fail('PROVIDER_STATE_CHANGED');
 const body={schema:'cerebro.core.supervisor.v1',...scope,request_id:id,status:'CORE_SUPERVISOR_VERIFIED',provider_terminal:true,iam_revoked:true,tribunal_signature_verified:true,fact_persisted:true,grant_sha256:hashes.grant,result_sha256:h,fact_sha256:hashes.fact,jarvis_mac_bound:tb.jarvis_mac,jarvis_hash_independently_verified:true,jarvis_sha256:hashes.jarvis,retry_allowed:false,promotion_allowed:false,checked_at_epoch:now()};return{body,signature:await signBody(priv,body)};
}

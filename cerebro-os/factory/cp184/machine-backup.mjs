const fail=s=>{throw Error(s)}, enc=new TextEncoder(), now=()=>Math.floor(Date.now()/1000), hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const canonical=o=>enc.encode(JSON.stringify(o,Object.keys(o).sort()));
const digest=async o=>hex(await crypto.subtle.digest('SHA-256',canonical(o)));
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const scope=Object.freeze({company_id:'fenix',engine_id:'FACT-001',environment:'LAB',capability:'FACT.INVENTORY.READ',read_only:true,external_mutation_allowed:false,cost_ceiling_eur:0});
const id='CP180-PRIVATE-PAIR-001', mac=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x), fresh=(t,n=now())=>Number.isSafeInteger(t)&&t>=0&&t<=n&&n-t<=30;
const decode=s=>{if(typeof s!=='string'||s.length>200||!/^[A-Za-z0-9+/]+={0,2}$/.test(s))fail('KEY_DENIED');return Uint8Array.from(atob(s),c=>c.charCodeAt(0));};
const publicKey=s=>crypto.subtle.importKey('raw',decode(s),{name:'Ed25519'},true,['verify']);
const verify=async(k,b,s)=>typeof s==='string'&&/^[a-f0-9]{128}$/.test(s)&&crypto.subtle.verify('Ed25519',k,Uint8Array.from(s.match(/../g),h=>parseInt(h,16)),canonical(b));
export const expectedEvidence=Object.freeze({jarvis_receipt_sha256:'6fcd3a290aad9b2a7c94204e091b445a7c2addcd62bcf63c7adc37ca1eda300d',fact_receipt_sha256:'c4171819c28c9c363681a25c82bd32b2685b56a7de31a93f60e799326f5be081',grant_sha256:'96168d77531ea3f2c5fdd71c2b619cecd1735d2739a473907752af4bbdf68a32',result_sha256:'5d482c8f9dfe8dbe24b59a095242d802df82e29b871a5a30b88def91a2c0533f'});
export async function backup(env,ports,expected=expectedEvidence,clock=now){
 if(env.CP184_MACHINE_ENABLED!=='true')fail('MACHINE_REVOKED');
 const ap=await publicKey(env.AUTHORITY_PUBLIC),tp=await publicKey(env.TRIBUNAL_PUBLIC),mp=await publicKey(env.MACHINE_PUBLIC),priv=await crypto.subtle.importKey('pkcs8',decode(env.MACHINE_PRIVATE),{name:'Ed25519'},false,['sign']);
 if(new Set([env.AUTHORITY_PUBLIC,env.TRIBUNAL_PUBLIC,env.MACHINE_PUBLIC,env.FACT_PUBLIC,env.JARVIS_PUBLIC]).size!==5)fail('ROLE_KEY_COLLISION');
 const q={...scope,domain:'CP181_PRIVATE_RPC_V1',action:'inspect',request_id:id,nonce:crypto.randomUUID(),emitted_at_epoch:clock()},s=hex(await crypto.subtle.sign('Ed25519',priv,canonical(q)));
 if(!await verify(mp,q,s))fail('MACHINE_KEY_MISMATCH');
 const [state,authority,tribunal]=await Promise.all([ports.jarvis.inspect(q,s),ports.iam.observe(q,s),ports.tribunal.inspect(q,s)]);
 const ab=authority?.body,tb=tribunal?.proof?.body,jr=state?.receipt,fr=tribunal?.fact,r=state?.reservation;
 if(!r||!exact(r,{request_id:id,state:'COMPLETED',created:r.created,terminal:r.terminal})||!Number.isSafeInteger(r.created)||!Number.isSafeInteger(r.terminal)||r.terminal<r.created||!jr||!fr||!ab||!tb||!mac(jr.mac)||!mac(fr.mac)||!fresh(ab.checked_at_epoch,clock())||!exact(ab,{...scope,request_id:id,role:'IAM',nonce:q.nonce,active:false,revoked:true,grant_sha256:ab.grant_sha256,checked_at_epoch:ab.checked_at_epoch})||ab.grant_sha256!==expected.grant_sha256||!await verify(ap,ab,authority.signature)||!exact(tb,{...scope,request_id:id,role:'TRIBUNAL',status:'VERIFIED_AUTHORIZED_PAIR',iam_grant_verified:true,promotion_allowed:false,jarvis_mac:jr.mac,fact_mac:fr.mac,result_sha256:fr.body.result_sha256,checked_at_epoch:tb.checked_at_epoch})||!Number.isSafeInteger(tb.checked_at_epoch)||tb.checked_at_epoch>clock()||!await verify(tp,tb,tribunal.proof.signature)||await digest(jr.body)!==expected.jarvis_receipt_sha256||await digest(fr.body)!==expected.fact_receipt_sha256||tb.result_sha256!==expected.result_sha256)fail('BACKUP_EVIDENCE_DENIED');
 return {status:'CP184_SIGNED_LOGICAL_BACKUP',request_id:id,environment:'LAB',machine_fingerprint:hex(await crypto.subtle.digest('SHA-256',decode(env.MACHINE_PUBLIC))),snapshot:{reservation:r,jarvis:jr,fact:fr,authority,tribunal:tribunal.proof},hashes:expected,promotion_allowed:false};
}

// CP181: private RPC adapters for CP180. No HTTP routes or deployment.
import {scope,principal,signBody,verifyBody} from '../cp169/independent-iam.mjs';
import {cp180RequestId as id} from '../cp169/bounded-store.mjs';
import {cp131Scope} from '../cp176/receipt-ports.mjs';
import {createFactService,createTribunal,createBoundedJarvis} from '../cp177/live-pair.mjs';
import {createRunLedger,createOneShot} from '../cp178/one-shot.mjs';
const clockNow=()=>Math.floor(Date.now()/1000), fail=s=>{throw Error(s)};
const exact=(a,b)=>a&&typeof a==='object'&&!Array.isArray(a)&&Object.keys(a).sort().join('|')===Object.keys(b).sort().join('|')&&Object.entries(b).every(([k,v])=>a[k]===v);
const mac=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const nonceOk=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{8,128}$/.test(x);
const fresh=(t,now)=>Number.isSafeInteger(t)&&Number.isSafeInteger(now)&&t>=0&&t<=now&&now-t<=30;
const request={...cp131Scope,request_id:id,principal_id:principal,policy_receipt_ref:'policy://cp166/'+id};
const actions=['run','inspect','verify-pair','current','persisted'];
export function rpcBody(action,nonce,t,jarvisMac,factMac){
 if(!actions.includes(action)||!nonceOk(nonce)||!Number.isSafeInteger(t)||t<0)fail('RPC_COMMAND_DENIED');
 const b={...scope,domain:'CP181_PRIVATE_RPC_V1',action,request_id:id,nonce,emitted_at_epoch:t};
 if(action==='verify-pair'){if(!mac(jarvisMac)||!mac(factMac))fail('RPC_PAIR_DENIED');return {...b,jarvis_mac:jarvisMac,fact_mac:factMac};}
 if(jarvisMac!==undefined||factMac!==undefined)fail('RPC_COMMAND_DENIED');
 return b;
}
async function authorize(key,action,q,sig,clock,j,f){
 if(!fresh(q?.emitted_at_epoch,clock())||!nonceOk(q?.nonce)||!exact(q,rpcBody(action,q.nonce,q.emitted_at_epoch,j,f))||!await verifyBody(key,q,sig)||!fresh(q.emitted_at_epoch,clock()))fail('RPC_CALLER_DENIED');
}
async function separate(...keys){
 const seen=new Set();for(const k of keys){if(k?.type!=='public'||k.algorithm?.name!=='Ed25519'||!k.usages.includes('verify'))fail('RPC_KEY_DENIED');const raw=Array.from(new Uint8Array(await crypto.subtle.exportKey('raw',k))).join(',');if(seen.has(raw))fail('RPC_ROLE_KEYS_NOT_DISTINCT');seen.add(raw);}
}
async function assertOwn(privateKey,publicKey){if(privateKey?.extractable!==false)fail('RPC_PRIVATE_KEY_DENIED');const q={domain:'CP181_ROLE_PROOF',nonce:crypto.randomUUID()};if(!await verifyBody(publicKey,q,await signBody(privateKey,q)))fail('RPC_ROLE_KEY_MISMATCH');}
export function createReceiptStore(storage,role){
 if(!['JARVIS','FACT-001'].includes(role)||!storage?.sql||typeof storage.transactionSync!=='function')fail('RPC_DURABLE_STORE_DENIED');
 const sql=storage.sql;sql.exec("CREATE TABLE IF NOT EXISTS cp181_receipt (id TEXT PRIMARY KEY, role TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('RESERVED','COMPLETED')), payload TEXT)");
 const row=()=>{if(sql.exec('SELECT id FROM cp181_receipt WHERE id<>? OR role<>? LIMIT 1',id,role).toArray().length)fail('RPC_STORAGE_SCOPE_DENIED');return sql.exec('SELECT state,payload FROM cp181_receipt WHERE id=? AND role=?',id,role).toArray()[0]??null;};
 const check=x=>{if(x!==id)fail('RPC_STORAGE_SCOPE_DENIED');};
 return Object.freeze({reserve(x){check(x);if(role!=='FACT-001')fail('RPC_RESERVE_DENIED');return storage.transactionSync(()=>{if(row())return false;sql.exec("INSERT INTO cp181_receipt VALUES (?,?,'RESERVED',NULL)",id,role);return true;});},
 insertOnce(x,payload){check(x);if(payload?.body?.request_id!==id||payload?.body?.origin!==role||!mac(payload?.mac))fail('RPC_RECEIPT_SCOPE_DENIED');return storage.transactionSync(()=>{const r=row();if(role==='FACT-001'){if(r?.state!=='RESERVED'||r.payload!==null)return false;sql.exec("UPDATE cp181_receipt SET state='COMPLETED',payload=? WHERE id=? AND role=?",JSON.stringify(payload),id,role);}else{if(r)return false;sql.exec("INSERT INTO cp181_receipt VALUES (?,?,'COMPLETED',?)",id,role,JSON.stringify(payload));}return true;});},
 get(x){check(x);const r=row();return r?.state==='COMPLETED'?JSON.parse(r.payload):null;}});
}
export async function createPrivateFactPort({db,iam,jarvisPublic,authorityPublic,factPublic,factPrivate,tribunalPublic,receiptKey,store,clock=clockNow}={}){
 await separate(jarvisPublic,authorityPublic,factPublic,tribunalPublic);await assertOwn(factPrivate,factPublic);
 if(typeof store?.reserve!=='function')fail('RPC_FACT_RESERVATION_REQUIRED');
 const fact=createFactService({db,iam,jarvisPublic,authorityPublic,factPrivate,receiptKey,store,clock,canaryId:id});
 return Object.freeze({async read(r,sig){const t=r?.emitted_at_epoch;const expected={...scope,request_id:id,principal_id:principal,policy_receipt_ref:request.policy_receipt_ref,version:'1.0.0',emitted_at_epoch:t};if(!fresh(t,clock())||!exact(r,expected)||!await verifyBody(jarvisPublic,r,sig)||!fresh(t,clock()))fail('RPC_FACT_CALLER_DENIED');if(await store.reserve(id)!==true)fail('RPC_FACT_ALREADY_RESERVED');return fact.read(r,sig);},
 async current(q,sig){await authorize(tribunalPublic,'current',q,sig,clock);return fact.current(q.nonce);},
 async persisted(q,sig){await authorize(tribunalPublic,'persisted',q,sig,clock);return fact.persisted(id);}});
}
export async function createPrivateTribunalPort({jarvisPublic,factPublic,authorityPublic,tribunalPublic,tribunalPrivate,jarvisVerifyKey,factVerifyKey,fact,clock=clockNow}={}){
 await separate(jarvisPublic,factPublic,authorityPublic,tribunalPublic);await assertOwn(tribunalPrivate,tribunalPublic);
 if(typeof fact?.current!=='function'||typeof fact?.persisted!=='function')fail('RPC_FACT_PORT_REQUIRED');
 const call=async(action,n)=>{const q=rpcBody(action,n,clock());return fact[action](q,await signBody(tribunalPrivate,q));};
 const tribunal=createTribunal({jarvisVerifyKey,factVerifyKey,authorityPublic,factReader:{current:n=>call('current',n),persisted:()=>call('persisted',crypto.randomUUID())},clock,canaryId:id});
 return Object.freeze({async verify(j,f,q,sig){await authorize(jarvisPublic,'verify-pair',q,sig,clock,j?.mac,f?.mac);return tribunal.verify(j,f);}});
}
export async function createPrivateJarvisPort({ingressPublic,jarvisPublic,jarvisPrivate,factPublic,authorityPublic,tribunalPublic,receiptKey,store,ledger,iam,fact,tribunal,clock=clockNow}={}){
 await separate(ingressPublic,jarvisPublic,factPublic,authorityPublic,tribunalPublic);await assertOwn(jarvisPrivate,jarvisPublic);
 if(typeof ledger?.inspect!=='function'||typeof store?.get!=='function'||typeof tribunal?.verify!=='function')fail('RPC_JARVIS_PORTS_REQUIRED');
 return Object.freeze({async run(q,sig){
 await authorize(ingressPublic,'run',q,sig,clock);
 const ownerAccess=async r=>exact(r,request)&&fresh(q.emitted_at_epoch,clock());
 const runner=createBoundedJarvis({iam,fact,jarvisPrivate,factPublic,receiptKey,store,ownerAccess,clock,canaryId:id,tribunal:{async verify(j,f){const b=rpcBody('verify-pair',crypto.randomUUID(),clock(),j.mac,f.mac);return tribunal.verify(j,f,b,await signBody(jarvisPrivate,b));}}});
 return createOneShot({ledger,runner,clock,canaryId:id}).run();},
 async inspect(q,sig){await authorize(ingressPublic,'inspect',q,sig,clock);return {reservation:await ledger.inspect(),receipt:await store.get(id)};}});
}
export function createJarvisStorage(storage){return {store:createReceiptStore(storage,'JARVIS'),ledger:createRunLedger(storage,{canaryId:id})};}

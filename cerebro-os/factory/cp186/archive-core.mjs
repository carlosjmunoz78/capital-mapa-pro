const fail=m=>{throw Error(m)}, enc=new TextEncoder(), hex=b=>Array.from(new Uint8Array(b),x=>x.toString(16).padStart(2,'0')).join('');
const stable=v=>v===null||typeof v!=='object'?v:Array.isArray(v)?v.map(stable):Object.fromEntries(Object.keys(v).sort().map(k=>[k,stable(v[k])]));
export const archiveHash=async v=>hex(await crypto.subtle.digest('SHA-256',enc.encode(JSON.stringify(stable(v)))));
const canonical=v=>enc.encode(JSON.stringify(v,Object.keys(v).sort()));
const bodyHash=async v=>hex(await crypto.subtle.digest('SHA-256',canonical(v)));
const sigVerify=async (key,p)=>p?.body&&typeof p.signature==='string'&&/^[a-f0-9]{128}$/.test(p.signature)&&await crypto.subtle.verify('Ed25519',key,Uint8Array.from(p.signature.match(/../g),x=>parseInt(x,16)),canonical(p.body));
const raw=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const pub=s=>crypto.subtle.importKey('raw',raw(s),{name:'Ed25519'},false,['verify']);
const id='CP180-PRIVATE-PAIR-001', scope={company_id:'fenix',engine_id:'FACT-001',environment:'LAB',capability:'FACT.INVENTORY.READ',read_only:true,external_mutation_allowed:false,cost_ceiling_eur:0,request_id:id};
const mac=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
const matches=(a,b)=>a&&Object.entries(b).every(([k,v])=>a[k]===v);
const same=(a,b)=>JSON.stringify(stable(a))===JSON.stringify(stable(b));
export const expected={archive:'64093be2a2499023cc56c10ae8bcb7fe4d7a65babf06e1a0fc5efe367489b7f1',machine:'66510ec6b4155495f0c22fd09c59d1f21784a931f14750e088373cbcd863f40d',hashes:{jarvis_receipt_sha256:'6fcd3a290aad9b2a7c94204e091b445a7c2addcd62bcf63c7adc37ca1eda300d',fact_receipt_sha256:'c4171819c28c9c363681a25c82bd32b2685b56a7de31a93f60e799326f5be081',grant_sha256:'96168d77531ea3f2c5fdd71c2b619cecd1735d2739a473907752af4bbdf68a32',result_sha256:'5d482c8f9dfe8dbe24b59a095242d802df82e29b871a5a30b88def91a2c0533f'}};
export async function validateArchive(xs,keys,contract=expected){
 if(!Array.isArray(xs)||xs.length!==2||await archiveHash(xs)!==contract.archive||keys.IAM===keys.TRIBUNAL)fail('ARCHIVE_INTEGRITY_DENIED');
 const ak=await pub(keys.IAM),tk=await pub(keys.TRIBUNAL), nonces=new Set();
 for(const x of xs){
  const s=x?.snapshot,r=s?.reservation,j=s?.jarvis,f=s?.fact,a=s?.authority,t=s?.tribunal;
  if(!matches(x,{status:'CP184_SIGNED_LOGICAL_BACKUP',request_id:id,environment:'LAB',machine_fingerprint:contract.machine,promotion_allowed:false})||!same(x.hashes,contract.hashes)||!matches(r,{request_id:id,state:'COMPLETED'})||!Number.isSafeInteger(r.created)||!Number.isSafeInteger(r.terminal)||r.terminal<r.created||!matches(j?.body,scope)||!matches(f?.body,scope)||!mac(j.mac)||!mac(f.mac)||await bodyHash(j.body)!==contract.hashes.jarvis_receipt_sha256||await bodyHash(f.body)!==contract.hashes.fact_receipt_sha256||f.body.result_sha256!==contract.hashes.result_sha256||!matches(a?.body,{...scope,role:'IAM',active:false,revoked:true,grant_sha256:contract.hashes.grant_sha256})||typeof a.body.nonce!=='string'||nonces.has(a.body.nonce)||!Number.isSafeInteger(a.body.checked_at_epoch)||a.body.checked_at_epoch<r.terminal||!matches(t?.body,{...scope,role:'TRIBUNAL',status:'VERIFIED_AUTHORIZED_PAIR',iam_grant_verified:true,promotion_allowed:false,jarvis_mac:j.mac,fact_mac:f.mac,result_sha256:contract.hashes.result_sha256})||!Number.isSafeInteger(t.body.checked_at_epoch)||!await sigVerify(ak,a)||!await sigVerify(tk,t))fail('SIGNED_EVIDENCE_DENIED');nonces.add(a.body.nonce);
 }
 for(const k of ['reservation','jarvis','fact','tribunal'])if(!same(xs[0].snapshot[k],xs[1].snapshot[k]))fail('BACKUP_PAIR_DRIFT');
 return {status:'CP186_LOGICAL_ARCHIVE_RESTORED',archive_sha256:contract.archive,records:6,signatures_verified:4,roles:4,grant_revoked:true,reservation:'COMPLETED',promotion_allowed:false};
}
const names=['reservation','jarvis','fact','tribunal','authority-1','authority-2'];
function rows(xs){return [...names.slice(0,4).map(k=>[k,xs[0].snapshot[k]]),['authority-1',xs[0].snapshot.authority],['authority-2',xs[1].snapshot.authority]];}
export async function restoreArchive(storage,xs,keys,contract=expected){
 await validateArchive(xs,keys,contract);
 const sql=storage.sql;sql.exec('CREATE TABLE IF NOT EXISTS cp186_archive (ordinal INTEGER PRIMARY KEY CHECK(ordinal IN (1,2)),payload TEXT NOT NULL)');sql.exec('CREATE TABLE IF NOT EXISTS cp186_evidence (name TEXT PRIMARY KEY,payload TEXT NOT NULL)');
 storage.transactionSync(()=>{if(sql.exec('SELECT count(*) n FROM cp186_archive').toArray()[0].n!==0||sql.exec('SELECT count(*) n FROM cp186_evidence').toArray()[0].n!==0)fail('RESTORE_ALREADY_EXISTS');for(const [i,x] of xs.entries())sql.exec('INSERT INTO cp186_archive VALUES (?,?)',i+1,JSON.stringify(x));for(const [k,x] of rows(xs))sql.exec('INSERT INTO cp186_evidence VALUES (?,?)',k,JSON.stringify(x));});
 return readArchive(storage,keys,contract);
}
export async function readArchive(storage,keys,contract=expected){
 const sql=storage.sql,xs=sql.exec('SELECT ordinal,payload FROM cp186_archive ORDER BY ordinal').toArray();
 if(xs.length!==2||xs[0].ordinal!==1||xs[1].ordinal!==2)fail('RESTORE_ROW_COUNT_DENIED');
 const snapshots=xs.map(x=>JSON.parse(x.payload)),records=sql.exec('SELECT name,payload FROM cp186_evidence ORDER BY name').toArray();
 if(records.length!==6||!same(records.map(x=>[x.name,JSON.parse(x.payload)]),rows(snapshots).sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0)))fail('RESTORE_RECORD_DRIFT');
 return validateArchive(snapshots,keys,contract);
}

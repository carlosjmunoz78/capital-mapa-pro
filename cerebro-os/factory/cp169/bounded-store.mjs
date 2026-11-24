// CP168: bounded Cloudflare Durable Object SQLite port for CP166.
export const requestId='CP168-PRIVATE-READ-001';
export const maxAcceptedNonces=12;
export const cp180RequestId='CP180-PRIVATE-PAIR-001';
export function assertCanaryId(value){if(value!==requestId&&value!==cp180RequestId)throw Error('CANARY_ID_DENIED');return value;}
export function createBoundedStore(storage,{canaryId=requestId}={}){
 const boundId=assertCanaryId(canaryId);
 if(!storage?.sql||typeof storage.transactionSync!=='function')throw Error('DURABLE_STORAGE_REQUIRED');
 const sql=storage.sql;
 sql.exec('CREATE TABLE IF NOT EXISTS cp168_grant (id TEXT PRIMARY KEY, body TEXT NOT NULL)');
 sql.exec('CREATE TABLE IF NOT EXISTS cp168_nonces (nonce TEXT PRIMARY KEY, action TEXT NOT NULL)');
 return Object.freeze({transition(action,id,nonce,grant,t){
  if(id!==boundId||!['issue','current','revoke'].includes(action)||typeof nonce!=='string'||!/^[A-Za-z0-9_.:-]{8,128}$/.test(nonce)||!Number.isSafeInteger(t))throw Error('CANARY_BOUNDARY_DENIED');
  return storage.transactionSync(()=>{
   if(sql.exec('SELECT id FROM cp168_grant WHERE id<>? LIMIT 1',boundId).toArray().length)throw Error('CANARY_STORAGE_SCOPE_DENIED');
   if(sql.exec('SELECT nonce FROM cp168_nonces WHERE nonce=?',nonce).toArray().length)throw Error('NONCE_REPLAY');
   const count=sql.exec('SELECT count(*) AS n FROM cp168_nonces').toArray()[0].n;
   // Reserve one terminal operation for revocation, even if the read quota is exhausted.
   if(action!=='revoke'&&count>=maxAcceptedNonces-1)throw Error('CANARY_QUOTA_EXHAUSTED');
   const rows=sql.exec('SELECT body FROM cp168_grant WHERE id=?',id).toArray(),g=rows.length===1?JSON.parse(rows[0].body):null;
   if(action==='issue'){
    if(g||!grant||grant.request_id!==id||grant.company_id!=='fenix'||grant.environment!=='LAB')throw Error('GRANT_ALREADY_EXISTS_OR_SCOPE_DENIED');
    sql.exec('INSERT INTO cp168_grant VALUES (?,?)',id,JSON.stringify(grant));
   }else if(action==='current'){
    if(!g||g.revoked||!g.active||g.expires_at_epoch<=t)throw Error('GRANT_INACTIVE');
   }else{
    if(!g)throw Error('GRANT_ABSENT');
    if(g.revoked)return g;
    sql.exec('UPDATE cp168_grant SET body=? WHERE id=?',JSON.stringify({...g,active:false,revoked:true}),id);
   }
   sql.exec('INSERT INTO cp168_nonces VALUES (?,?)',nonce,action);return g;
  });
 }});
}

// CP178 additive, fail-closed one-shot guard. Fixed LAB canary; never renew or retry work.
import {requestId,assertCanaryId} from '../cp169/bounded-store.mjs';
const fail=s=>{throw Error(s)};
export function createRunLedger(storage,{canaryId=requestId}={}){
 const requestId=assertCanaryId(canaryId);
 if(!storage?.sql||typeof storage.transactionSync!=='function')fail('DURABLE_STORAGE_REQUIRED');
 const sql=storage.sql;sql.exec("CREATE TABLE IF NOT EXISTS cp178_run (id TEXT PRIMARY KEY, owner TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('RUNNING','COMPLETED','HOLD')), created INTEGER NOT NULL, terminal INTEGER)");
 const get=()=>{if(sql.exec('SELECT id FROM cp178_run WHERE id<>? LIMIT 1',requestId).toArray().length)fail('CANARY_LEDGER_SCOPE_DENIED');return sql.exec('SELECT id,owner,state,created,terminal FROM cp178_run WHERE id=?',requestId).toArray()[0]??null;};
 return Object.freeze({claim(owner,now){if(typeof owner!=='string'||!Number.isSafeInteger(now))fail('CLAIM_INVALID');return storage.transactionSync(()=>{if(get())return false;sql.exec("INSERT INTO cp178_run VALUES (?,?,'RUNNING',?,NULL)",requestId,owner,now);return true})},
 finish(owner,state,now){if(!['COMPLETED','HOLD'].includes(state)||!Number.isSafeInteger(now))fail('FINISH_INVALID');return storage.transactionSync(()=>{const r=get();if(!r||r.owner!==owner||r.state!=='RUNNING'||now<r.created)fail('FENCE_DENIED');sql.exec('UPDATE cp178_run SET state=?,terminal=? WHERE id=? AND owner=? AND state=?',state,now,requestId,owner,'RUNNING');return true})},
 inspect(){const r=get();return r?{request_id:r.id,state:r.state,created:r.created,terminal:r.terminal}:null}});
}
export function createOneShot({ledger,runner,clock=()=>Math.floor(Date.now()/1000),canaryId=requestId}={}){
 const requestId=assertCanaryId(canaryId);
 if(typeof ledger?.claim!=='function'||typeof ledger?.finish!=='function'||typeof runner?.run!=='function')fail('PORTS_REQUIRED');
 return Object.freeze({async run(){
 const owner=crypto.randomUUID();if(await ledger.claim(owner,clock())!==true)fail('ALREADY_RESERVED_NO_RETRY');
 let out;
 try{out=await runner.run();if(out?.status!=='CP177_PAIR_VERIFIED_AND_REVOKED'||out.grant_revoked!==true||out.promotion_allowed!==false||out.result?.request_id!==requestId||out.result?.company_id!=='fenix'||out.result?.environment!=='LAB')fail('RESULT_DENIED');}
 catch(e){await ledger.finish(owner,'HOLD',clock());throw e;}
 // Ambiguous commit or crash leaves RUNNING or COMPLETED; neither can execute again.
 if(await ledger.finish(owner,'COMPLETED',clock())!==true)fail('TERMINAL_PERSISTENCE_UNKNOWN');
 return {status:'CP178_ONE_SHOT_COMPLETED',request_id:requestId,grant_revoked:true,promotion_allowed:false};
 }});
}
// A HOLD or RUNNING row is never proof of revocation. Resolve only via independent
// IAM evidence and verified quiescence of the old runner; do not reset this row.
// This guard does not make revocation atomic with a distributed read.

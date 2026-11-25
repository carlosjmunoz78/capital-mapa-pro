import {DurableObject,WorkerEntrypoint} from 'cloudflare:workers';
import {createFact} from './private-clients.mjs';
import {verifyBody} from './independent-iam.mjs';
import {requestId} from './bounded-store.mjs';
import {publicKey,privateKey} from './key-import.mjs';
export const statusBody=()=>({purpose:'CP169_RECEIPT_READBACK',request_id:requestId,company_id:'fenix',environment:'LAB'});
const fail=s=>{throw Error(s)};
export class GrantLedger extends DurableObject{
 constructor(ctx,env){super(ctx,env);this.ctx=ctx;this.sql=ctx.storage.sql;this.sql.exec('CREATE TABLE IF NOT EXISTS cp169_receipt (id TEXT PRIMARY KEY, payload TEXT)');}
 reserve(){return this.ctx.storage.transactionSync(()=>{if(this.sql.exec('SELECT id FROM cp169_receipt WHERE id=?',requestId).toArray().length)fail('ONE_SHOT_ALREADY_USED');this.sql.exec('INSERT INTO cp169_receipt(id,payload) VALUES (?,NULL)',requestId);return true;});}
 store(payload){return this.ctx.storage.transactionSync(()=>{const r=this.sql.exec('SELECT payload FROM cp169_receipt WHERE id=?',requestId).toArray();if(r.length!==1||r[0].payload!==null)fail('RECEIPT_ALREADY_USED');this.sql.exec('UPDATE cp169_receipt SET payload=? WHERE id=?',JSON.stringify(payload),requestId);return true;});}
 inspect(){const r=this.sql.exec('SELECT payload FROM cp169_receipt WHERE id=?',requestId).toArray();return !r.length?{state:'NOT_RUN'}:!r[0].payload?{state:'RESERVED'}:{state:'PERSISTED',...JSON.parse(r[0].payload)};}
}
export class FactInventoryLab extends WorkerEntrypoint{
 #ledger(){if(this.env.CP169_ENABLED!=='true'||!this.env.RECEIPTS||!this.env.IAM||!this.env.RECOVERY_DB)fail('DISABLED');const n=this.env.RECEIPTS.jurisdiction('eu');return n.get(n.idFromName('fenix-cp169-fact-receipt'));}
 async read(r,sig){if(r?.request_id!==requestId||r?.company_id!=='fenix'||r?.environment!=='LAB'||r?.policy_receipt_ref!=='policy://cp166/'+requestId)fail('SCOPE_DENIED');const [j,a,f]=await Promise.all([publicKey(this.env.JARVIS_PUBLIC),publicKey(this.env.AUTHORITY_PUBLIC),privateKey(this.env.FACT_PRIVATE)]);if(!await verifyBody(j,r,sig))fail('CALLER_DENIED');const l=this.#ledger();await l.reserve();const reader=createFact({db:this.env.RECOVERY_DB,iam:this.env.IAM,jarvisPublic:j,authorityPublic:a,factPrivate:f});const out=await reader.read(r,sig);await l.store(out);return out;}
 async inspect(r,sig){const e=statusBody();if(!r||Object.keys(r).sort().join('|')!==Object.keys(e).sort().join('|')||Object.entries(e).some(([k,v])=>r[k]!==v)||!await verifyBody(await publicKey(this.env.JARVIS_PUBLIC),r,sig))fail('CALLER_DENIED');return this.#ledger().inspect();}
}
export default {async fetch(){return new Response(null,{status:404,headers:{'cache-control':'no-store'}})}};

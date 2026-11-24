import {DurableObject,WorkerEntrypoint} from 'cloudflare:workers';
import {createFactoryCandidateReader} from './fact001_inventory_read_cp162.mjs';
import {principal,issuer,id,ref,scope,now,request,control,exact,makeGrant,current,revoked,sign,verify,hash} from './authority.mjs';
const deny=c=>{throw Error(c)};
export class GrantLedger extends DurableObject{
 constructor(ctx,env){super(ctx,env);this.ctx=ctx;this.sql=ctx.storage.sql;this.sql.exec('CREATE TABLE IF NOT EXISTS proof (id TEXT PRIMARY KEY,grant_json TEXT NOT NULL,receipt_json TEXT,receipt_mac TEXT)');}
 issue(r){return this.ctx.storage.transactionSync(()=>{if(this.sql.exec('SELECT id FROM proof WHERE id=?',id).toArray().length)deny('ONE_SHOT_ALREADY_USED');const g=makeGrant(r);this.sql.exec('INSERT INTO proof(id,grant_json) VALUES(?,?)',id,JSON.stringify(g));return g;});}
 getGrant(){const a=this.sql.exec('SELECT grant_json FROM proof WHERE id=?',id).toArray();if(a.length!==1)deny('GRANT_ABSENT');return current(JSON.parse(a[0].grant_json));}
 store(r,mac){return this.ctx.storage.transactionSync(()=>{this.getGrant();const a=this.sql.exec('SELECT receipt_json FROM proof WHERE id=?',id).toArray();if(a.length!==1||a[0].receipt_json!==null)deny('RECEIPT_ALREADY_USED');this.sql.exec('UPDATE proof SET receipt_json=?,receipt_mac=? WHERE id=?',JSON.stringify(r),mac,id);return true;});}
 readReceipt(){const a=this.sql.exec('SELECT grant_json,receipt_json,receipt_mac FROM proof WHERE id=?',id).toArray();if(!a.length)return {state:'NOT_RUN'};const g=JSON.parse(a[0].grant_json);return {state:g.revoked?'REVOKED':g.expires_at_epoch<=now()?'EXPIRED':'ISSUED',receipt:a[0].receipt_json?JSON.parse(a[0].receipt_json):null,mac:a[0].receipt_mac};}
 revoke(){return this.ctx.storage.transactionSync(()=>{const a=this.sql.exec('SELECT grant_json FROM proof WHERE id=?',id).toArray();if(a.length!==1)deny('GRANT_ABSENT');const g=revoked(JSON.parse(a[0].grant_json));this.sql.exec('UPDATE proof SET grant_json=? WHERE id=?',JSON.stringify(g),id);return true;});}
}
export class FactInventoryLab extends WorkerEntrypoint{
 #ledger(){if(this.env.CP164_ENABLED!=='true'||!this.env.GRANTS||!this.env.RECOVERY_DB||this.env.JARVIS_KEY===this.env.FACT_RECEIPT_KEY)deny('DISABLED');const ns=this.env.GRANTS.jurisdiction('eu');return ns.get(ns.idFromName('fenix-cp164-one-shot'));}
 async execute(r,p){if(!exact(r,request())||!await verify(this.env.JARVIS_KEY,r,p))deny('CALLER_DENIED');const l=this.#ledger();await l.issue(r);const read=createFactoryCandidateReader({db:this.env.RECOVERY_DB,authenticateJarvis:async(q,x)=>verify(this.env.JARVIS_KEY,q,x),readCurrentGrant:async(x)=>{if(x!==ref)deny('REF_DENIED');return l.getGrant();},principalId:principal,issuerId:issuer});const result=await read(r,p);const receipt={...scope,request_id:id,version:'1.0.0',principal_id:principal,policy_receipt_ref:ref,schema:'cerebro.private-read.v1',origin:'FACT-001',target:'JARVIS',status:'COMPLETED',emitted_at_epoch:now(),result_sha256:await hash(result),candidate_count:result.count};const mac=await sign(this.env.FACT_RECEIPT_KEY,receipt);await l.store(receipt,mac);return {result,receipt,receipt_persisted:true};}
 async inspect(r,p){if(!exact(r,control('inspect'))||!await verify(this.env.JARVIS_KEY,r,p))deny('CALLER_DENIED');const a=await this.#ledger().readReceipt();if(a.receipt&&!await verify(this.env.FACT_RECEIPT_KEY,a.receipt,a.mac))deny('RECEIPT_MAC_DENIED');return {state:a.state,receipt:a.receipt??null,receipt_mac_verified:!!a.receipt};}
 async revoke(r,p){if(!exact(r,control('revoke'))||!await verify(this.env.JARVIS_KEY,r,p))deny('CALLER_DENIED');return this.#ledger().revoke();}
}
export default {async fetch(){return new Response(null,{status:404,headers:{'cache-control':'no-store'}});}};

import test from 'node:test';
import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createGuard} from './zero-cost-guard.mjs';
const account='a'.repeat(32);
const day=86400*20000;
const order=n=>({company_id:'fenix',engine_id:'FACT-001',environment:'PREPROD',version:'1.1.0',capability:'FACT.INVENTORY.READ',request_id:'CORE-PREPROD-20261124-00'+n});
const plan=t=>({account_id:account,plan:'WORKERS_FREE',observed_at_epoch:t,source:'synthetic-test-only',products:['workers','durable_objects_sqlite','workflows'],external_paid_services:false});
function storage(db){return {sql:{exec(q,...args){const s=db.prepare(q);if(/^SELECT/.test(q))return {toArray:()=>s.all(...args)};s.run(...args);return {toArray:()=>[]};}},transactionSync(f){db.exec('BEGIN IMMEDIATE');try{const v=f();db.exec('COMMIT');return v;}catch(e){db.exec('ROLLBACK');throw e;}}};}
function fixture(t,opts={}){
 const dir=mkdtempSync(join(tmpdir(),'core-finops-')),file=join(dir,'ledger.sqlite');let db=new DatabaseSync(file),now=day+1,observed=plan(now),calls=0;
 const config=()=>({storage:storage(db),accountId:account,readTrustedPlan:async()=>observed,clock:()=>now,dailyLimit:2,...opts});
 let g=createGuard(config());
 t.after(()=>{db.close();rmSync(dir,{recursive:true,force:true});});
 return {submit:(o,fn)=>g.submit(o,fn??(async id=>{calls++;return {request_id:id,instance_id:id.toLowerCase()};})),calls:()=>calls,plan:p=>observed=p,time:n=>now=n,reopen:()=>{db.close();db=new DatabaseSync(file);g=createGuard(config());}};
}
test('free plan submits exactly once and reservation persists across reopen',async t=>{const f=fixture(t);assert.equal((await f.submit(order(2))).status,'SUBMITTED');f.reopen();assert.equal((await f.submit(order(2))).reason,'DUPLICATE_RECONCILE_NO_RETRY');assert.equal(f.calls(),1);});
test('daily cap defers and resets UTC, old ID never reusable',async t=>{const f=fixture(t);await f.submit(order(2));await f.submit(order(3));const r=await f.submit(order(4));assert.equal(r.status,'DEFER');assert.equal(r.retry_after_epoch,day+86400);f.time(day+86400);f.plan(plan(day+86400));assert.equal((await f.submit(order(4))).status,'SUBMITTED');assert.equal((await f.submit(order(2))).reason,'DUPLICATE_RECONCILE_NO_RETRY');});
test('paid, unknown, stale or future plan fails closed',async t=>{const f=fixture(t);for(const p of [null,{...plan(day),plan:'PAID'},plan(day-86400),plan(day+2),{...plan(day),account_id:'b'.repeat(32)}]){f.plan(p);assert.equal((await f.submit(order(2))).reason,'FREE_PLAN_UNVERIFIED');}assert.equal(f.calls(),0);});
test('external paid service or incomplete products denied',async t=>{const f=fixture(t);for(const p of [{...plan(day),external_paid_services:true},{...plan(day),products:['workers']}]){f.plan(p);assert.equal((await f.submit(order(2))).status,'HOLD');}assert.equal(f.calls(),0);});
test('scope and historical request denied before submission',async t=>{const f=fixture(t);for(const o of [order(1),{...order(2),environment:'PROD'},{...order(2),company_id:'other'},{...order(2),capability:'WRITE'},{...order(2),cost:0}])assert.equal((await f.submit(o)).reason,'SCOPE_DENIED');assert.equal(f.calls(),0);});
test('ambiguous submission preserves reservation and forbids retry',async t=>{const f=fixture(t);assert.equal((await f.submit(order(2),async()=>({}))).reason,'SUBMISSION_AMBIGUOUS_NO_RETRY');assert.equal((await f.submit(order(2))).reason,'DUPLICATE_RECONCILE_NO_RETRY');});
test('provider error never retries or falls back to paid',async t=>{const f=fixture(t);assert.equal((await f.submit(order(2),async()=>{throw Error('quota');})).reason,'SUBMISSION_FAILED_RECONCILE_NO_RETRY');assert.equal((await f.submit(order(2))).reason,'DUPLICATE_RECONCILE_NO_RETRY');});
test('concurrent duplicate only submits once',async t=>{const f=fixture(t);const rs=await Promise.all([f.submit(order(2)),f.submit(order(2))]);assert.equal(rs.filter(x=>x.status==='SUBMITTED').length,1);assert.equal(f.calls(),1);});
test('trusted plan unavailable blocks',async t=>{const f=fixture(t,{readTrustedPlan:async()=>{throw Error('offline');}});assert.equal((await f.submit(order(2))).status,'HOLD');assert.equal(f.calls(),0);});
test('guard never authorizes promotion',async t=>{const f=fixture(t);assert.equal((await f.submit(order(2))).promotion_allowed,false);});

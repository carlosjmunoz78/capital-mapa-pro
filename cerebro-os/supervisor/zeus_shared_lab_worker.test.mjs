import assert from "node:assert/strict";
import {test} from "node:test";
import {classifyP5,utcDay,runZeusTick,CHECKS} from "./zeus_shared_lab_worker.mjs";
const check=CHECKS[0],day="20261123",now=Date.UTC(2026,10,23,10,0);
const config={automation_id:check.automation_id,company_id:check.company_id,engine_id:check.engine_id,environment:"LAB",version:"1.0.0",enabled:1,max_daily_jobs:1};
const job={request_id:"FACT001-P5-"+day,day_key:day,company_id:check.company_id,engine_id:check.engine_id,environment:"LAB",version:"1.0.0",operation:check.operation,max_cost_eur:0,state:"COMPLETED",attempts:1,completed_at_ms:now-10000};
class FakeDB{
  constructor(data){this.data=data;this.events=new Map();this.sql=[];}
  prepare(sql){this.sql.push(sql);let args;return{bind:(...params)=>{args=params;return{first:async()=>{if(sql.includes("automation_registry"))return this.data.config;if(sql.includes("WHERE request_id"))return this.data.job;if(sql.includes("COUNT(*)"))return {n:this.data.reconciles};throw Error("UNEXPECTED_SELECT");},run:async()=>{if(!sql.includes("INSERT INTO cerebro_zeus_supervisor_events_lab_v1"))throw Error("ILLEGAL_WRITE");if(this.events.has(args[0]))return{meta:{changes:0}};this.events.set(args[0],args);return{meta:{changes:1}};}}}}}
}
function env(data={}){return {ZEUS_SUPERVISOR_ENABLED:"true",SUPERVISOR_DB:new FakeDB({config,job,reconciles:0,...data})};}
test("valid actual scope classified healthy",()=>assert.equal(classifyP5({config,job,newReconciles:0},check).code,"P5_DAILY_COMPLETED"));
test("bad config fails closed",()=>assert.equal(classifyP5({config:{...config,enabled:0},job,newReconciles:0},check).code,"AUTOMATION_CONFIG_DRIFT"));
test("new reconcile detected, historical excluded in SQL",()=>assert.equal(classifyP5({config,job,newReconciles:1},check).code,"NEW_RECONCILE"));
test("unverified completion blocked",()=>assert.equal(classifyP5({config,job:{...job,attempts:0},newReconciles:0},check).code,"P5_COMPLETION_UNVERIFIED"));
test("job company crossover blocked",()=>assert.equal(classifyP5({config,job:{...job,company_id:"aion"},newReconciles:0},check).code,"JOB_SCOPE_DRIFT"));
test("no daily job is incident",()=>assert.equal(classifyP5({config,job:null,newReconciles:0},check).code,"P5_DAILY_MISSING"));
test("no observation before 02:00 UTC",async()=>assert.equal((await runZeusTick(env(),Date.UTC(2026,10,23,1,59))).status,"BEFORE_P5_DUE"));
test("disabled always off",async()=>assert.equal((await runZeusTick({ZEUS_SUPERVISOR_ENABLED:"false"},now)).status,"OFF"));
test("first real observation and duplicate tick dedupe",async()=>{
 const e=env(); const first=await runZeusTick(e,now),again=await runZeusTick(e,now+60000);
 assert.equal(first.checks[0].inserted,1);assert.equal(again.checks[0].inserted,0);
 assert.equal(e.SUPERVISOR_DB.events.size,1);
 assert.equal(e.SUPERVISOR_DB.sql.filter(x=>/INSERT/.test(x)).length,2);
 assert.equal(e.SUPERVISOR_DB.sql.some(x=>/UPDATE|DELETE|INSERT INTO fact001_/i.test(x)),false);
});
test("new incident is separate immutable event",async()=>{
 const e=env();await runZeusTick(e,now);e.SUPERVISOR_DB.data.reconciles=1;
 const x=await runZeusTick(e,now+60000);assert.equal(x.checks[0].status,"INCIDENT");
 assert.equal(e.SUPERVISOR_DB.events.size,2);
});
test("no HTTP route divulges internal health",async()=>{
 const mod=await import("./zeus_shared_lab_worker.mjs");
 assert.equal((await mod.default.fetch()).status,404);
});
test("UTC day formatting",()=>assert.equal(utcDay(now),"20261123"));
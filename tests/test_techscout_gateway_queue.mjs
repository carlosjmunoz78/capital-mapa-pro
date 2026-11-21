import test from "node:test";
import assert from "node:assert/strict";
import gateway from "../cerebro-os/engines/TECH-SCOUT/gateway-queue.mjs";

const queueName="cerebro-techscout-gateway-one-shot-lab-eu";
const makeBody=(changes={})=>({
 company_id:"fenix-capital",engine_id:"TECH-SCOUT",environment:"LAB",
 version:"0.1.0",capability:"TECHSCOUT.PROBE",provider:"WORLD_BANK",
 request_id:"techscout_gateway_unittest_20261121_1",...changes
});
function fixture({enabled=true,service=true,store=true,failAudit=false,failRpc=false}={}){
 const events=[],data=new Map(),calls=[];
 const kv=store?{
  get:async key=>data.has(key)?data.get(key):null,
  put:async(key,value)=>{if(failAudit)throw Error("KV");data.set(key,value);events.push({kind:"AUDIT",key})}
 }:null;
 const env={
  TECHSCOUT_GATEWAY_ENABLED:enabled?"true":"false",
  TECHSCOUT_CALLER_TOKEN:"TEST_"+"s".repeat(64),
  LAB_KV:kv,
  TECHSCOUT:service?{
    probePublic:async(body,token)=>{calls.push({body,token});if(failRpc)throw Error("RPC");return {status:"PASS",http:200,shape_ok:true}}
  }:null
 };
 const message=(body=makeBody())=>({
  body,ackCount:0,retryCount:0,ack(){this.ackCount++},retry(){this.retryCount++}
 });
 return {env,calls,data,events,message};
}
const batch=(m,name=queueName)=>({queue:name,messages:[m]});

test("GET cannot expose a public API",async()=>{
 const r=await gateway.fetch();
 assert.equal(r.status,403);
});
test("foreign queue is rejected",async()=>{
 const f=fixture(),m=f.message();
 await assert.rejects(gateway.queue(batch(m,"other-queue"),f.env),/QUEUE_DENIED/);
 assert.equal(m.ackCount,0);
});
test("disabled: no RPC and retried instead of executed",async()=>{
 const f=fixture({enabled:false}),m=f.message();
 await gateway.queue(batch(m),f.env);
 assert.equal(m.retryCount,1);assert.equal(f.calls.length,0);
});
test("invalid company is denied without storage or RPC",async()=>{
 const f=fixture(),m=f.message(makeBody({company_id:"other-tenant"}));
 await gateway.queue(batch(m),f.env);
 assert.equal(m.ackCount,1);assert.equal(f.calls.length,0);assert.equal(f.data.size,0);
});
test("invalid environment is denied",async()=>{
 const f=fixture(),m=f.message(makeBody({environment:"PROD"}));
 await gateway.queue(batch(m),f.env);
 assert.equal(m.ackCount,1);assert.equal(f.calls.length,0);assert.equal(f.data.size,0);
});
test("provider allowlist blocks arbitrary providers",async()=>{
 const f=fixture(),m=f.message(makeBody({provider:"UNKNOWN"}));
 await gateway.queue(batch(m),f.env);
 assert.equal(m.ackCount,1);assert.equal(f.calls.length,0);
});
test("success has gateway audit and private service RPC",async()=>{
 const f=fixture(),m=f.message();
 await gateway.queue(batch(m),f.env);
 assert.equal(m.ackCount,1);assert.equal(f.calls.length,1);
 assert.equal(f.events.length,2);
 const data=JSON.parse([...f.data.values()][0]);
 assert.equal(data.status,"PASS");assert.equal(data.http,200);assert.equal(data.company_id,"fenix-capital");
 assert.equal(JSON.stringify(data).includes("TEST_ssss"),false);
});
test("duplicate receipt is not re-executed",async()=>{
 const f=fixture(),m=f.message(),dup=f.message();
 await gateway.queue(batch(m),f.env);
 await gateway.queue(batch(dup),f.env);
 assert.equal(f.calls.length,1);assert.equal(dup.ackCount,1);assert.equal(f.events.length,2);
});
test("source RPC failure is audited and blocked",async()=>{
 const f=fixture({failRpc:true}),m=f.message();
 await gateway.queue(batch(m),f.env);
 const result=JSON.parse([...f.data.values()][0]);
 assert.equal(result.status,"BLOCKED");assert.equal(result.reason,"SERVICE_RPC_FAILED");
 assert.equal(m.ackCount,1);
});
test("audit unavailable denies before RPC",async()=>{
 const f=fixture({failAudit:true}),m=f.message();
 await gateway.queue(batch(m),f.env);
 assert.equal(m.retryCount,1);assert.equal(f.calls.length,0);
});
test("missing secret or target Worker fails closed",async()=>{
 for(const extra of [{service:false},{enabled:false}]){
  const f=fixture(extra),m=f.message();
  await gateway.queue(batch(m),f.env);
  assert.equal(m.retryCount,1);
 }
});

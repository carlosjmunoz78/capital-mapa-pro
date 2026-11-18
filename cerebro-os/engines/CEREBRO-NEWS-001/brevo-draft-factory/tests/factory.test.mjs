import test from "node:test";
import assert from "node:assert/strict";
import {createHash} from "node:crypto";
import {TARGETS,validate,build,prepare} from "../factory.mjs";
function html(){
 let s='<html><body><img src="https://fenixcapital.es/wp-content/uploads/logo.png"><img src="https://fenixcapital.es/wp-content/uploads/hero.jpg">';
 for(let i=0;i<10;i++)s+='<div data-block="b'+i+'"></div>';
 for(let i=0;i<13;i++)s+='<a href="https://fenixcapital.es/a'+i+'">A</a>';
 return s+"{{ unsubscribe }}</body></html>";
}
function report(h=html()){const sum=createHash("sha256").update(h).digest("hex");return {engine_id:"CEREBRO-NEWS-001",environment:"LAB",send_enabled:false,publish_enabled:false,approved:false,api_called:false,weekly_campaign_suffix:"2026w47",audiences:{b2b:{brevo:{status:"LAB_PASS",html_sha256:sum},subject:"B2B",preheader:"Pro"},b2c:{brevo:{status:"LAB_PASS",html_sha256:sum},subject:"B2C",preheader:"Pers"}}};}
test("target only B2B=18 B2C=17",()=>assert.deepEqual(TARGETS,{b2b:18,b2c:17}));
test("full design passes",()=>assert.equal(validate("b2b",html(),report()).listId,18));
test("reject old cohort",()=>assert.throws(()=>validate("legacy",html(),report()),/BAD_AUDIENCE/));
test("reject missing sections",()=>{let s=html().replace(/<div data-block="b9"><\/div>/,"");assert.throws(()=>validate("b2c",s,report(s)),/MISSING_10/);});
test("reject no unsubscribe",()=>{let s=html().replace("{{ unsubscribe }}","");assert.throws(()=>validate("b2c",s,report(s)),/UNSUBSCRIBE/);});
test("reject wrong checksum",()=>assert.throws(()=>validate("b2b",html(),report("junk")),/HASH/));
test("reject missing brand image",()=>{let s=html().replace("https://fenixcapital.es/wp-content/uploads/logo.png","data:image/png;base64,x");assert.throws(()=>validate("b2b",s,report(s)),/ASSETS/);});
test("reject live flag",()=>{let x=report();x.send_enabled=true;assert.throws(()=>validate("b2b",html(),x),/NOT_SAFE/);});
test("payload new lists and no send action",()=>{let p=build("b2c",html(),report());assert.deepEqual(p.recipients.listIds,[17]);assert.equal("scheduledAt" in p,false);assert.equal("sendNow" in p,false);});
test("OFF by default, no network and no key",async()=>{let calls=0;const x=await prepare({enable:false,dir:"/missing",fetcher:async()=>{calls++;}});assert.equal(x.apiCalled,false);assert.equal(calls,0);});
test("enabled requires key",async()=>{await assert.rejects(prepare({enable:true,key:"",dir:"/missing"}),/NO_BREVO/);});

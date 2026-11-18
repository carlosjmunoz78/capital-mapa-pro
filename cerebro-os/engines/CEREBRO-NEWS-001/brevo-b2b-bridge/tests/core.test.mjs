import test from "node:test";
import assert from "node:assert/strict";
import {clean,salinas,classify,allowed,audit} from "../core.mjs";
const c=(id,company,extra={})=>({id,email:"test"+id+"@example.org",attributes:{COMPANY:company},emailBlacklisted:false,...extra});
const reader=(data={})=>async path=>{
 const listId=Number(path.match(/lists\/(\d+)/)?.[1]),offset=Number(path.match(/offset=(\d+)/)?.[1]);
 return {contacts:(data[listId]||[]).slice(offset,offset+50)};
};
test("allowed source IDs only",()=>{
 assert.equal(allowed("/contacts/lists/9/contacts?limit=50&offset=0"),true);
 assert.equal(allowed("/contacts/lists/10/contacts?limit=50&offset=0"),false);
 assert.equal(allowed("/emailCampaigns"),false);
});
test("no query injection",()=>assert.equal(allowed("/contacts/lists/9/contacts?limit=50&offset=0&secret=123"),false));
test("normalize accent",()=>assert.equal(clean("SÁLINAS"),"salinas"));
test("salinas by agency name",()=>assert.equal(salinas(c(1,"Inmobiliaria Salinas")),true));
test("salinas by different attribute",()=>assert.equal(salinas({attributes:{NOMBRE_EMPRESA:"Salinas"} }),true));
test("salinas by email",()=>assert.equal(salinas({email:"salinas@dominio.es"}),true));
test("other agencies not salinas",()=>assert.equal(salinas(c(2,"Agencia Alba")),false));
test("hard bounce or blacklist blocks",()=>assert.equal(classify(c(1,"Agencia Alba",{emailBlacklisted:true})),"EXCLUDE_BLOCKED"));
test("unknown block state holds",()=>assert.equal(classify(c(1,"Agencia Alba",{emailBlacklisted:null})),"HOLD_UNKNOWN_BLOCKING"));
test("missing agency holds",()=>assert.equal(classify(c(1,"")),"HOLD_UNKNOWN_COMPANY"));
test("no marketing send authorization from membership",()=>assert.equal(classify(c(1,"Agencia Alba")),"CANDIDATE_CONSENT_NOT_PROVEN"));
test("dedupe, Salinas, blacklists",async()=>{
 const result=await audit(reader({9:[c(1,"Agencia Alba"),c(2,"Salinas")],13:[c(1,"Agencia Alba"),c(3,"Agencia L",{emailBlacklisted:true})]}));
 assert.equal(result.unique_contact_ids,3);assert.equal(result.duplicate_memberships,1);
 assert.equal(result.reasons.EXCLUDE_SALINAS,1);assert.equal(result.reasons.EXCLUDE_BLOCKED,1);
 assert.equal(result.send_authorized,false);assert.equal(result.includes_personal_data,false);
});
test("no data exported",async()=>{
 const r=await audit(reader({9:[c(4,"Salinas",{email:"salinas@private.example"})]}));
 assert.equal(JSON.stringify(r).includes("private.example"),false);
});
test("provider invalid response blocks",async()=>{await assert.rejects(audit(async()=>({foo:[]})),/BAD_API_RESPONSE/);});
test("pagination limit blocks",async()=>{
 await assert.rejects(audit(async()=>({contacts:Array.from({length:50},(_,i)=>c(i+1,"Agencia"))}),{maxPages:1}),/PAGINATION_LIMIT/);
});
test("pure module has no send or mutate functions",async()=>{
 const mod=await import("../core.mjs");
 for(const s of ["sendCampaign","createCampaign","addContactToList","deleteContact"])assert.equal(s in mod,false);
});

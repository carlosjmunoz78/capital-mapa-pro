import test from "node:test";
import assert from "node:assert/strict";
import {TARGET_IDS,htmlCheck,summarizeCampaign,summarizeTemplate,summarizeTemplates,auditDecision} from "../core.mjs";
test("fixed owners and no historical recipients",()=>assert.deepEqual(TARGET_IDS.lists,[17,18]));
test("html structure count",()=>{const h="<a></a>".repeat(13)+"<img>".repeat(2)+'<tr data-block="x"></tr>'.repeat(10)+"{{ unsubscribe }}";const c=htmlCheck(h);assert.equal(c.ten_modules,true);assert.equal(c.link_count,13);assert.equal(c.image_count,2);assert.equal(c.brevo_unsubscribe_expression,true);});
test("campaign only fixed id",()=>assert.throws(()=>summarizeCampaign({id:9},112),/BAD_CAMPAIGN/));
test("campaign no personal address leaked",()=>{const s=summarizeCampaign({id:112,name:"A",htmlContent:"<html>secret@example.com</html>",subject:"Sub",recipients:{listIds:[17]}},112);assert.equal("htmlContent" in s,false);assert.equal("email" in s,false);assert.deepEqual(s.list_ids,[17]);});
test("template active state",()=>{assert.equal(summarizeTemplate({id:115,isActive:false,sender:{email:"a@b.c"}},115).is_active,false);});
test("templates filter names",()=>{const s=summarizeTemplates({templates:[{id:1,name:"OTHER"},{id:115,name:"NEWS001 B2C",isActive:true}]});assert.equal(s.news001_candidates.length,1);});
test("audit holds until proven",()=>{const a=auditDecision({campaign_b2b:{subject_present:true,html_present:true},campaign_b2c:{subject_present:true,html_present:true},template_b2c:{is_active:true}});assert.equal(a.commercial_sending_authorized,false);assert.equal(a.b2b_automation_message_exists,false);});

test("B2B canonical automation template is #114",()=>assert.equal(TARGET_IDS.template_b2b,114));

test("operator source export remains private and targets only four existing marketing drafts",async()=>{const {readFileSync}=await import("node:fs");const s=readFileSync(new URL("../index.ts",import.meta.url),"utf8");assert.ok(s.includes('mode==="export"'));assert.ok(s.includes('"/emailCampaigns/113"'));assert.ok(s.includes('"/smtp/templates/114"'));assert.ok(!s.includes('"/contacts"'));});

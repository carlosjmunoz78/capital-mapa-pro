import test from "node:test";import assert from "node:assert/strict";import {eligibleTestCampaign,OWNER} from "../test-send.mjs";
import {HTML_B2B,HTML_B2C} from "../canonical.mjs";
test("only owner test mailbox",()=>assert.equal(OWNER,"carlosj.munozcabeza@gmail.com"));
test("B2B test protects audiences",()=>{const x=eligibleTestCampaign(113,{id:113,status:"draft",recipients:{lists:[18]},sender:{email:"hipotecas@fenixcapital.es"},htmlContent:HTML_B2B});assert.equal(x.sending_to_contacts,false);});
test("B2C test protects audiences",()=>{const x=eligibleTestCampaign(112,{id:112,status:"draft",recipients:{lists:[17]},sender:{email:"hipotecas@fenixcapital.es"},htmlContent:HTML_B2C});assert.equal(x.authorized_test_email,OWNER);});
test("reject wrong audience",()=>assert.throws(()=>eligibleTestCampaign(113,{id:113,status:"draft",recipients:{lists:[10,18]},sender:{email:"hipotecas@fenixcapital.es"},htmlContent:HTML_B2B}),/WRONG_RECIPIENT/));
test("reject prod sent campaign",()=>assert.throws(()=>eligibleTestCampaign(112,{id:112,status:"sent",recipients:{lists:[17]},sender:{email:"hipotecas@fenixcapital.es"},htmlContent:HTML_B2C}),/NOT_DRAFT/));

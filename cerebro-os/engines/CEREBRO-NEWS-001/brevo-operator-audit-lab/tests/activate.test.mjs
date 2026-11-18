import test from "node:test";import assert from "node:assert/strict";
import {eligibleTemplate} from "../activate.mjs";
import {HTML_B2B,HTML_B2C} from "../canonical.mjs";
test("B2B can be activated only with correct complete existing HTML",()=>assert.equal(eligibleTemplate(114,{id:114,isActive:false,htmlContent:HTML_B2B,sender:{email:"hipotecas@fenixcapital.es"}}).already_active,false));
test("B2C can be activated only with correct complete existing HTML",()=>assert.equal(eligibleTemplate(115,{id:115,isActive:false,htmlContent:HTML_B2C,sender:{email:"hipotecas@fenixcapital.es"}}).already_active,false));
test("all other IDs forbidden",()=>assert.throws(()=>eligibleTemplate(111,{id:111}),/NOT_ALLOWED/));
test("incomplete template rejected",()=>assert.throws(()=>eligibleTemplate(114,{id:114,isActive:false,htmlContent:"short",sender:{email:"hipotecas@fenixcapital.es"}}),/QA_NOT_GREEN/));
test("foreign sender rejected",()=>assert.throws(()=>eligibleTemplate(115,{id:115,isActive:false,htmlContent:HTML_B2C,sender:{email:"other@example.com"}}),/SENDER/));

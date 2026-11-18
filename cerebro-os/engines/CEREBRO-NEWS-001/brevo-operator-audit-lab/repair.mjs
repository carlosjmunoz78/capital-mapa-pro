// Fails closed. New canonical HTML from verified 18/11/2026 generated artifact; only four exact existing draft assets.
// All original Brevo assets backed up before updates in commit 931afd65dfe3ff36087d72e15a1134d01d27260b.
import {HTML_B2B,HTML_B2C,META} from "./canonical.mjs";
export const TARGETS=Object.freeze({
 campaign_b2c_112:{path:"/emailCampaigns/112",kind:"b2c",previousChars:10182,type:"campaign",id:112},
 campaign_b2b_113:{path:"/emailCampaigns/113",kind:"b2b",previousChars:3164,type:"campaign",id:113},
 template_b2b_114:{path:"/smtp/templates/114",kind:"b2b",previousChars:3134,type:"template",id:114},
 template_b2c_115:{path:"/smtp/templates/115",kind:"b2c",previousChars:9474,type:"template",id:115}
});
const SNAPSHOT="931afd65dfe3ff36087d72e15a1134d01d27260b";
export function prepare(target,old){
 const t=TARGETS[target];
 if(!t||!old||Number(old.id)!==t.id)throw Error("TARGET_OR_SOURCE_MISMATCH");
 const html=t.kind==="b2b"?HTML_B2B:HTML_B2C;
 const m=META[t.kind];
 if(typeof old.htmlContent!=="string")throw Error("OLD_HTML_MISSING");
 if(t.type==="campaign"&&String(old.status||old.campaignStatus).toLowerCase()!=="draft")throw Error("CAMPAIGN_NOT_DRAFT");
 if(t.type==="template"&&old.isActive!==false)throw Error("TEMPLATE_NOT_INACTIVE");
 if(old.htmlContent===html)return {target,path:t.path,method:"PUT",already_done:true,payload:null};
 if(old.htmlContent.length!==t.previousChars)throw Error("SOURCE_CHANGED_ABORT");
 if(!html.includes("{{ unsubscribe }}")||(html.match(/data-block=/g)||[]).length!==10||
    (html.match(/<a(?:\s|>)/g)||[]).length!==13||
    (html.match(/<img(?:\s|>)/g)||[]).length!==2)throw Error("CANONICAL_SOURCE_NOT_VALIDATED");
 const payload=t.type==="campaign"
   ?{subject:m.subject,previewText:m.preheader,htmlContent:html,recipients:{listIds:[m.listId]}}
   :{subject:m.subject,htmlContent:html,isActive:false};
 if(JSON.stringify(payload).includes('"scheduledAt"')||Object.keys(payload).includes("sendNow"))throw Error("SEND_NOT_ALLOWED");
 return {target,path:t.path,method:"PUT",already_done:false,payload,precondition_backup_commit:SNAPSHOT};
}
export function verify(target,remote){
 const t=TARGETS[target];
 if(!t||!remote||Number(remote.id)!==t.id)throw Error("VERIFY_WRONG_ID");
 const html=String(remote.htmlContent||"");
 return {target,id:t.id,verified_full_length:html.length>=12000,html_chars:html.length,
   sufficient_links:(html.match(/<a(?:\s|>)/gi)||[]).length>=13,
   image_count:(html.match(/<img(?:\s|>)/gi)||[]).length,
   unsub_token:html.includes("{{ unsubscribe }}"),
   campaign_still_draft:t.type!=="campaign"||String(remote.status||remote.campaignStatus).toLowerCase()==="draft",
   template_still_inactive:t.type!=="template"||remote.isActive===false,
   send_executed:false};
}

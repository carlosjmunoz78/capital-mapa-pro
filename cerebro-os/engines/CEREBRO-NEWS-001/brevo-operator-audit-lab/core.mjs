// NEWS001 audit only; never write, contact import or send.
// The function owner extracts summary metadata, never returns any HTML or PII.
export const TARGET_IDS=Object.freeze({campaign_b2c:112,campaign_b2b:113,template_b2c:115,lists:[17,18]});
export function htmlCheck(html){
 const s=typeof html==="string"?html:"";
 const blockCount=(s.match(/\bdata-block=/gi)||[]).length;
 const links=(s.match(/<a(?:\s|>)/gi)||[]).length;
 const img=(s.match(/<img(?:\s|>)/gi)||[]).length;
 return {html_present:s.length>100,html_chars:s.length,
   ten_modules:blockCount===10,link_count:links,image_count:img,
   link_baja_placeholder:s.includes("{{ unsubscribe }}"),
   brevo_unsubscribe_expression:/{{\s*unsubscribe\s*}}|\/mk\/un\//i.test(s),
   original_logo_candidate:/logo-fenix|fenix-capital-oficial/i.test(s),
   content_warning:/data:image\/|<script\b|href=["']javascript:/i.test(s)};
}
export function summarizeCampaign(c,id){
 if(!c||typeof c!=="object"||Number(c.id)!==id)throw Error("BAD_CAMPAIGN_ID");
 const recipients=c.recipients&&typeof c.recipients==="object"?c.recipients:{};
 const listIds=Array.isArray(recipients.lists)?recipients.lists:Array.isArray(recipients.listIds)?recipients.listIds:[];
 return {id,name:String(c.name||"").slice(0,180),
  status:String(c.status||c.campaignStatus||"UNKNOWN"),
  list_ids:listIds.filter(Number.isInteger),
  exclude_list_ids:Array.isArray(recipients.exclusionListIds)?recipients.exclusionListIds.filter(Number.isInteger):[],
  sender_verified_in_account:false,subject_present:typeof c.subject==="string"&&c.subject.length>0,
  preview_present:typeof c.previewText==="string"&&c.previewText.length>0,
  ...htmlCheck(c.htmlContent)};
}
export function summarizeTemplate(t,id){
 if(!t||Number(t.id)!==id)throw Error("BAD_TEMPLATE_ID");
 return {id,is_active:t.isActive===true,name:String(t.name||t.templateName||"").slice(0,180),
  subject_present:typeof t.subject==="string"&&t.subject.length>0,
  sender_present:!!(t.sender?.email||t.sender?.id),...htmlCheck(t.htmlContent)};
}
export function summarizeTemplates(r){
 const a=Array.isArray(r?.templates)?r.templates:[];
 return {total_page_count:a.length,news001_candidates:a.filter(x=>/news001|f[eé]nix|hipoteca|inmobiliaria/i.test(String(x.name||x.templateName||"")))
   .map(x=>({id:x.id,name:String(x.name||x.templateName||"").slice(0,180),
      is_active:x.isActive===true,subject_present:!!x.subject})).slice(0,25)};
}
export function auditDecision(x){
 const b2c=x.campaign_b2c,b2b=x.campaign_b2b,t=x.template_b2c;
 return {b2c_draft_validated:!!(b2c?.subject_present&&b2c?.html_present),
  b2b_draft_validated:!!(b2b?.subject_present&&b2b?.html_present),
  b2c_automation_template_active:t?.is_active===true,
  b2b_automation_message_exists:false, // UI proof required; do not infer from campaign or templates
  commercial_sending_authorized:false,old_workflow_9_must_remain_active:true};
}
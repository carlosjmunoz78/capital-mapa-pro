// NEWS001 / Brevo lead sync, strict rules. No contact data in logs.
export const LISTS={particulares:17,inmobiliarias:18};
const EMAIL=/^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const HOLD=(reason)=>({state:"HOLD",reason});
export function plan(x,now=new Date()){
 if(!x||x.action!=="sync"||x.company_id!=="fenix"||x.marketing_consent!==true||x.source_marketing_consent!==true)return HOLD("CONSENT_OR_ORIGIN_MISSING");
 if(x.origin!=="fenix_prod_web_lead_ingest"||x.synthetic!==false||x.active!==true)return HOLD("NOT_LIVE_WEB_LEAD");
 if(x.blocked===true||x.unsubscribed===true)return HOLD("LOCAL_SUPPRESSION");
 const when=new Date(x.lead_at||"");if(!Number.isFinite(when.getTime())||when.getTime()>now.getTime()+120000||now.getTime()-when.getTime()>45*60*1000)return HOLD("LEAD_TIMESTAMP_NOT_RECENT");
 const email=String(x.email||"").trim().toLowerCase();if(email.length>254||!EMAIL.test(email))return HOLD("INVALID_EMAIL");
 let u;try{u=new URL(x.landing_url)}catch{return HOLD("INVALID_LANDING_URL")};
 if(u.protocol!=="https:"||!["fenixcapital.es","www.fenixcapital.es"].includes(u.hostname)||u.username||u.password)return HOLD("BAD_LANDING_HOST");
 if(!u.pathname.startsWith("/"))return HOLD("BAD_PATH");
 const persona=u.pathname.startsWith("/inmobiliarias/")?"inmobiliarias":"particulares";
 if(x.profile!==persona)return HOLD("PROFILE_MISMATCH");
 if(persona==="inmobiliarias" && /salinas|sálinas|s[aá]linas/i.test(String(x.company_name||"")+" "+String(x.name||"")))return HOLD("EXCLUDED_COMPANY");
 return {state:"ELIGIBLE",email,list_id:LISTS[persona],persona,company_id:"fenix",engine_id:"CEREBRO-NEWS-001"};
}
export function gateContact(c,listId){
 if(!c||typeof c!=="object")return HOLD("REMOTE_STATUS_UNKNOWN");
 if(c.emailBlacklisted!==false)return HOLD("BREVO_BLACKLISTED_OR_UNKNOWN");
 if(!Array.isArray(c.listIds)||!Array.isArray(c.listUnsubscribed))return HOLD("BREVO_MEMBERSHIP_UNKNOWN");
 if(c.listUnsubscribed.includes(listId)||c.listUnsubscribed.some(x=>x===17||x===18))return HOLD("BREVO_PREVIOUS_OPTOUT");
 const other=listId===17?18:17;if(c.listIds.includes(other))return HOLD("OTHER_AUDIENCE_PRESENT");
 if(c.listIds.includes(listId))return {state:"ALREADY_SUBSCRIBED"};
 return {state:"SAFE_TO_ADD"};
}
export function redactResult(r){return {state:r.state,reason:r.reason||undefined,list_id:r.list_id||undefined,api_calls:r.api_calls||0,commercial_campaign_send:false}};

// CEREBRO-NEWS-001 / deterministically verified signup bridge (LAB only).
// Trusted ingestion adapter must independently authenticate form-origin evidence.
// Never treat arbitrary JSON, Brevo membership, privacy acceptance or CRM presence as opt-in.
export const LISTS=Object.freeze({particular:17,inmobiliaria:18});
export const CONSENT_VERSION='news001-optin-20261118';
const emailRE=/^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const hold=(reason)=>({state:'HOLD',reason,write_authorized:false,send_authorized:false});
function date(raw){if(typeof raw!=='string'||!/(?:Z|[+-]\d\d:\d\d)$/.test(raw))return null;const n=Date.parse(raw);return Number.isFinite(n)?n:null;}
export function classify(record,{activationAt='2026-11-18T18:00:00Z',now=new Date()}={}){
 if(!record||typeof record!=='object')return hold('INVALID_RECORD');
 if(record.company_id!=='fenix'||record.origin!=='fenix_cerebro_leads')return hold('WRONG_COMPANY_OR_ORIGIN');
 if(record.marketing_consent!==true||record.consent_privacy!==true)return hold('NEWSLETTER_OPTIN_MISSING');
 if(record.consent_text_version!==CONSENT_VERSION)return hold('UNVERIFIED_CONSENT_TEXT_VERSION');
 if(record.trusted_ingest_verified!==true||record.proof_signature_verified!==true||record.lead_form_verified!==true)return hold('INGEST_PROVENANCE_UNVERIFIED');
 if(typeof record.consent_evidence_id!=='string'||!/^news001-[a-f0-9]{32,64}$/.test(record.consent_evidence_id))return hold('EVIDENCE_ID_MISSING');
 const c=date(record.consent_at), a=date(activationAt), n=now.getTime();
 if(c===null||a===null||c<a||c>n+120000||n-c>7*86400000)return hold('OUTDATED_OR_UNVERIFIED_CONSENT');
 if(record.suppressed!==false||record.unsubscribed!==false||record.hard_bounced!==false)return hold('SUPPRESSION_UNKNOWN_OR_TRUE');
 const email=String(record.email||'').trim().toLowerCase();
 if(email.length>254||!emailRE.test(email))return hold('INVALID_EMAIL');
 let u;try{u=new URL(record.landing_url)}catch{return hold('INVALID_SOURCE_URL');}
 if(u.protocol!=='https:'||!['fenixcapital.es','www.fenixcapital.es'].includes(u.hostname)||u.username||u.password)return hold('UNVERIFIED_SOURCE_HOST');
 const persona=u.pathname.startsWith('/inmobiliarias/')?'inmobiliaria':'particular';
 if(record.persona!==persona||record.consent_purpose!==(persona==='inmobiliaria'?'b2b_newsletter':'b2c_newsletter'))return hold('PROFILE_OR_PURPOSE_MISMATCH');
 if(persona==='inmobiliaria'&&record.salinas_screened!==true)return hold('B2B_EXCLUSION_NOT_SCREENED');
 const val=(record.agency_name||'')+' '+(record.company_name||'')+' '+(record.name||'');
 if(/s[aá]linas/i.test(val.normalize('NFD').replace(/[\u0300-\u036f]/g,'')))return hold('EXCLUDED_AGENCY');
 return {state:'ELIGIBLE_FOR_TEST_ONLY',company_id:'fenix',engine_id:'CEREBRO-NEWS-001',persona,list_id:LISTS[persona],email,
  consent_evidence_id:record.consent_evidence_id,write_authorized:false,send_authorized:false};
}
function blockedBrevo(c,listId){
 if(!c||typeof c!=='object'||c.emailBlacklisted!==false||!Array.isArray(c.listIds)||!Array.isArray(c.listUnsubscribed||[]))return 'BREVO_STATUS_UNKNOWN';
 if(c.listUnsubscribed?.includes(listId)||c.listUnsubscribed?.includes(LISTS.particular)||c.listUnsubscribed?.includes(LISTS.inmobiliaria))return 'PREVIOUSLY_UNSUBSCRIBED';
 const other=listId===LISTS.particular?LISTS.inmobiliaria:LISTS.particular;
 if(c.listIds.includes(other))return 'PROFILE_CONFLICT';
 return null;
}
export async function sync({record,now=new Date(),activationAt,enabled=false,key='',fetcher=fetch,log=()=>{}}){
 const plan=classify(record,{activationAt,now});
 if(plan.state!=='ELIGIBLE_FOR_TEST_ONLY')return plan;
 if(!enabled||process.env.NEWS001_CONTACT_SYNC_ENABLED!=='true')return {...plan,state:'LAB_DRY_RUN',api_called:false};
 if(!key)throw Error('HOLD_BREVO_KEY_MISSING');
 if(record.runtime_release_approved!==true||record.proof_signature_verified!==true)throw Error('HOLD_RELEASE_NOT_VERIFIED');
 const api=async(path,method='GET',body)=>{
  if(!(/^\/contacts\/[^/]+$/.test(path)||path==='/contacts'))throw Error('HOLD_PATH_FORBIDDEN');
  if(!['GET','PUT','POST'].includes(method)||(method==='POST'&&path!=='/contacts')||(method==='PUT'&&path==='/contacts'))throw Error('HOLD_METHOD_FORBIDDEN');
  const res=await fetcher('https://api.brevo.com/v3'+path,{method,redirect:'error',headers:{'api-key':key,'content-type':'application/json','accept':'application/json'},...(body?{body:JSON.stringify(body)}:{})});
  if(res.status===404&&method==='GET')return {notFound:true};
  if(!res.ok)throw Error('HOLD_BREVO_HTTP_'+res.status);
  if(res.status===204)return {};
  return res.json();
 };
 const encoded=encodeURIComponent(plan.email);
 const current=await api('/contacts/'+encoded);
 if(!current.notFound){
  const block=blockedBrevo(current,plan.list_id);
  if(block)return hold(block);
  if(current.listIds.includes(plan.list_id))return {...plan,state:'ALREADY_IN_CORRECT_LIST',api_called:true,write_authorized:false};
 }
 // No EMAIL reassignment, no global blacklist clearing, no opt-out reset.
 if(current.notFound)await api('/contacts','POST',{email:plan.email,listIds:[plan.list_id],updateEnabled:false});
 else await api('/contacts/'+encoded,'PUT',{listIds:[plan.list_id]});
 const verified=await api('/contacts/'+encoded);
 if(verified.notFound||blockedBrevo(verified,plan.list_id)||!verified.listIds.includes(plan.list_id))throw Error('HOLD_REMOTE_VERIFICATION_FAILED');
 log({state:'CONTACT_LIST_VERIFIED',list_id:plan.list_id,consent_evidence_id:plan.consent_evidence_id}); // no PII in logs
 return {state:'CONTACT_LIST_VERIFIED',list_id:plan.list_id,consent_evidence_id:plan.consent_evidence_id,api_called:true,send_authorized:false};
}

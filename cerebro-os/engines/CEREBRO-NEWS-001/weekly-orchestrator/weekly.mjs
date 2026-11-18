import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {build} from '../brevo-draft-factory/factory.mjs';

// CEREBRO-NEWS-001: no recipients are ever read from a client-provided list.
// A send is possible only with a fresh externally attested and hash-pinned release proof.
export const COMPANY='fenix';
export const AUDIENCES=Object.freeze({b2b:18,b2c:17});
export const RELEASE_GATES=Object.freeze([
  'trusted_ingestion_e2e','marketing_consent_evidence','b2b_b2c_routing_e2e',
  'salinas_excluded','unsubscribes_respected','hard_bounces_excluded',
  'sender_verified','real_owner_inbox_e2e','sources_verified_current',
  'images_and_links_checked','brevo_free_quota_verified','old_vs_new_checked',
  'backup_verified','rollback_verified','tribunal_passed'
]);
const fail=(code)=>{throw new Error('HOLD_'+code);};
function parseDate(raw){const x=new Date(raw);if(typeof raw!=='string'||!Number.isFinite(x.getTime()))fail('BAD_DATE');return x;}
function differenceHours(later,earlier){return (later.getTime()-earlier.getTime())/3600000;}
export function isoWeek(d){
  const a=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate()));
  a.setUTCDate(a.getUTCDate()+4-(a.getUTCDay()||7));
  const y=a.getUTCFullYear();const start=new Date(Date.UTC(y,0,1));
  return `${y}w${String(Math.ceil((((a-start)/86400000)+1)/7)).padStart(2,'0')}`;
}
function offsetAt(d){
 const name=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',timeZoneName:'shortOffset'}).formatToParts(d).find(x=>x.type==='timeZoneName')?.value;
 const match=/GMT([+-])(\d{1,2})(?::(\d{2}))?/.exec(name||'');
 if(!match)fail('TIMEZONE');
 return (match[1]==='-'?-1:1)*(Number(match[2])*60+Number(match[3]||0));
}
export function nextSchedule(now,weekday=4,hour=10,minute=30){
 const start=new Date(Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate()));
 for(let i=0;i<15;i++){
   const localday=new Date(start.getTime()+i*86400000);
   if(localday.getUTCDay()!==weekday)continue;
   const localClock=Date.UTC(localday.getUTCFullYear(),localday.getUTCMonth(),localday.getUTCDate(),hour,minute);
   let utc=new Date(localClock - offsetAt(new Date(localClock))*60000);
   utc=new Date(localClock - offsetAt(utc)*60000); // DST boundary exact at target hour
   if(differenceHours(utc,now)>=8 && differenceHours(utc,now)<=168)return utc.toISOString().replace('.000Z','Z');
 }
 fail('NO_FUTURE_DELIVERY_WINDOW');
}
export function validateEditorial({dir,now}){
 const report=JSON.parse(readFileSync(join(dir,'RESULTADO_PRUEBA.json'),'utf8'));
 if(report.engine_id!=='CEREBRO-NEWS-001'||report.environment!=='LAB'||report.send_enabled!==false||report.publish_enabled!==false||report.approved!==false||report.api_called!==false)fail('EDITORIAL_REPORT_FLAGS');
 const generated=parseDate(report.date+'T12:00:00Z');
 if(differenceHours(now,generated)<-15||differenceHours(now,generated)>36)fail('STALE_OR_FUTURE_EDITORIAL');
 if(report.weekly_campaign_suffix!==isoWeek(generated)||report.weekly_campaign_suffix!==isoWeek(now))fail('WRONG_WEEK');
 if(report.content_origin!=='CEREBRO_DETERMINISTIC_VERIFIED_NEWS_FALLBACK_NOT_DEEPSEEK')fail('UNKNOWN_EDITORIAL_ORIGIN');
 const payloads={};
 for(const kind of ['b2b','b2c']){
   const html=readFileSync(join(dir,`NEWS_FENIX_${kind}_BREVO_BORRADOR.html`),'utf8');
   payloads[kind]=build(kind,html,report); // Existing 10-block, 13-link, 2-image + unsubscribe QA.
   if(payloads[kind].recipients.listIds.length!==1||payloads[kind].recipients.listIds[0]!==AUDIENCES[kind])fail('WRONG_LIST');
 }
 if(payloads.b2b.name===payloads.b2c.name)fail('SAME_CAMPAIGN_NAME');
 return {payloads,report};
}
export function validateRelease({release,raw,sha256,now,sendDate}){
 if(!raw||!sha256||createHash('sha256').update(raw).digest('hex')!==sha256)fail('RELEASE_PROOF_HASH');
 if(release.company_id!==COMPANY||release.engine_id!=='CEREBRO-NEWS-001'||release.environment!=='PROD'||release.approved!==true)fail('RELEASE_NOT_APPROVED');
 for(const g of RELEASE_GATES)if(release.gates?.[g]!==true)fail('GATE_'+g.toUpperCase());
 const checked=parseDate(release.verified_at);const target=parseDate(sendDate);
 if(differenceHours(now,checked)<0||differenceHours(now,checked)>24)fail('STALE_RELEASE_EVIDENCE');
 if(differenceHours(target,now)<8||differenceHours(target,now)>168)fail('BAD_SEND_WINDOW');
 if(release.provider!=='BREVO_FREE'||!Number.isInteger(release.available_daily_credits)||release.available_daily_credits<1||release.available_daily_credits>300)fail('QUOTA_PROOF');
 let total=0;
 for(const kind of ['b2b','b2c']){
   const c=release.cohorts?.[kind];
   if(c?.list_id!==AUDIENCES[kind]||c?.verified!==true||c?.consent_evidence_complete!==true||c?.suppression_check_complete!==true||!Number.isInteger(c?.recipients)||c.recipients<0)fail('COHORT_'+kind.toUpperCase());
   total+=c.recipients;
 }
 if(total<1||total>release.available_daily_credits||total>300)fail('EXCEEDS_FREE_CREDITS');
 return {total,credit_headroom:release.available_daily_credits-total};
}
export async function execute({dir,now=new Date(),mode='dry-run',key='',releasePath='',releaseSha256='',fetcher=fetch,log=()=>{}}){
 const {payloads,report}=validateEditorial({dir,now});
 const scheduleB2B=nextSchedule(now,4,10,30);
 const scheduleB2C=nextSchedule(now,4,11,0);
 if(mode==='dry-run')return {state:'LAB_DRY_RUN_NO_BREVO_CALLS',week:report.weekly_campaign_suffix,targets:AUDIENCES,schedule_b2b:scheduleB2B,schedule_b2c:scheduleB2C};
 if(mode!=='schedule'||process.env.NEWS001_SCHEDULE_ENABLED!=='true')fail('LIVE_SWITCH_OFF');
 if(!key||!releasePath||!releaseSha256)fail('MISSING_SECRET_OR_PROOF');
 const raw=readFileSync(releasePath,'utf8');const release=JSON.parse(raw);
 const eligibility=validateRelease({release,raw,sha256:releaseSha256,now,sendDate:scheduleB2B});
 if(!eligibility.total)fail('EMPTY_COHORTS');
 const api=async(path,method='GET',payload=null)=>{
   if(!/^\/emailCampaigns(?:\?type=classic&limit=100&offset=\d+|\/\d+)?$/.test(path))fail('API_NOT_ALLOWED');
   if(method!=='GET'&&!(method==='POST'&&path==='/emailCampaigns'))fail('API_METHOD_NOT_ALLOWED');
   const response=await fetcher('https://api.brevo.com/v3'+path,{method,headers:{'api-key':key,'content-type':'application/json','accept':'application/json'},...(payload?{body:JSON.stringify(payload)}:{})});
   if(!response.ok)fail(`BREVO_HTTP_${response.status}`);
   return response.json();
 };
 const existing=[];
 for(let offset=0;offset<=900;offset+=100){
   const data=await api(`/emailCampaigns?type=classic&limit=100&offset=${offset}`);
   if(!Array.isArray(data.campaigns))fail('INVALID_CAMPAIGN_LIST');
   existing.push(...data.campaigns);
   if(data.campaigns.length<100)break;
   if(offset===900)fail('PAGINATION_LIMIT');
 }
 const names=[payloads.b2b.name,payloads.b2c.name];
 if(existing.some(x=>names.includes(x.name)))fail('WEEK_ALREADY_EXISTS');
 const created=[];
 // Full preflight is complete before first network mutation; partial failures halt closed.
 for(const [kind,sendAt] of [['b2b',scheduleB2B],['b2c',scheduleB2C]]){
   const payload={...payloads[kind],scheduledAt:sendAt,tag:'NEWS001_PROD_WEEKLY'};
   const res=await api('/emailCampaigns','POST',payload);
   if(!Number.isInteger(res.id)||res.id<1)fail('CREATE_NO_CAMPAIGN_ID');
   created.push({kind,id:res.id,schedule_at:sendAt});
   log({state:'BREVO_CAMPAIGN_CREATED',kind,id:res.id});
 }
 // Verify both remote records, never claim success on POST alone.
 for(const item of created){
   const remote=await api(`/emailCampaigns/${item.id}`);
   if(remote.name!==payloads[item.kind].name||!['scheduled','scheduledAt'].includes(remote.status))fail('REMOTE_SCHEDULE_NOT_VERIFIED');
   const remoteLists=remote.recipients?.lists||remote.recipients?.listIds||[];
   if(remoteLists.length!==1||Number(remoteLists[0])!==AUDIENCES[item.kind])fail('REMOTE_RECIPIENTS_INVALID');
 }
 return {state:'TWO_WEEKLY_CAMPAIGNS_SCHEDULED_VERIFIED',week:report.weekly_campaign_suffix,created,cost_additional_eur:0};
}
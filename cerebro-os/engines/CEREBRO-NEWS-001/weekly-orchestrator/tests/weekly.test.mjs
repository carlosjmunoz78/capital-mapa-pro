import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {AUDIENCES,RELEASE_GATES,isoWeek,nextSchedule,validateEditorial,validateRelease,execute} from '../weekly.mjs';
const NOW=new Date('2026-11-18T19:00:00Z');
function html(){let x='<html><body><img src="https://fenixcapital.es/wp-content/uploads/logo.png"><img src="https://fenixcapital.es/wp-content/uploads/hero.jpg">';for(let i=0;i<10;i++)x+=`<div data-block="m${i}">Texto</div>`;for(let i=0;i<13;i++)x+=`<a href="https://fenixcapital.es/p${i}">Enlace</a>`;return x+'{{ unsubscribe }}</body></html>';}
function fixture(overrides={}){
 const dir=mkdtempSync(join(tmpdir(),'news001-weekly-'));
 const s=html(),sha=createHash('sha256').update(s).digest('hex');
 const report={engine_id:'CEREBRO-NEWS-001',environment:'LAB',send_enabled:false,publish_enabled:false,approved:false,api_called:false,date:'2026-11-18',weekly_campaign_suffix:'2026w47',content_origin:'CEREBRO_DETERMINISTIC_VERIFIED_NEWS_FALLBACK_NOT_DEEPSEEK',audiences:{b2b:{subject:'Asunto B2B',preheader:'Vista B2B',brevo:{status:'LAB_PASS',html_sha256:sha}},b2c:{subject:'Asunto B2C',preheader:'Vista B2C',brevo:{status:'LAB_PASS',html_sha256:sha}}},...overrides};
 writeFileSync(join(dir,'RESULTADO_PRUEBA.json'),JSON.stringify(report));
 for(const kind of ['b2c','b2b'])writeFileSync(join(dir,`NEWS_FENIX_${kind}_BREVO_BORRADOR.html`),s);
 return dir;
}
function approvedProof(patch={}){
 const p={company_id:'fenix',engine_id:'CEREBRO-NEWS-001',environment:'PROD',approved:true,verified_at:'2026-11-18T18:50:00Z',provider:'BREVO_FREE',available_daily_credits:300,gates:Object.fromEntries(RELEASE_GATES.map(g=>[g,true])),cohorts:{b2b:{list_id:18,verified:true,consent_evidence_complete:true,suppression_check_complete:true,recipients:1},b2c:{list_id:17,verified:true,consent_evidence_complete:true,suppression_check_complete:true,recipients:1}},...patch};
 const raw=JSON.stringify(p);return {release:p,raw,sha256:createHash('sha256').update(raw).digest('hex')};
}
test('reuses exact B2B #18 B2C #17 lists and current ISO week',()=>{assert.deepEqual(AUDIENCES,{b2b:18,b2c:17});assert.equal(isoWeek(NOW),'2026w47');const x=validateEditorial({dir:fixture(),now:NOW});assert.equal(x.payloads.b2b.recipients.listIds[0],18);assert.equal(x.payloads.b2c.recipients.listIds[0],17);});
test('Madrid time is maintained across DST',()=>{for(const n of [NOW,new Date('2027-07-07T12:00:00Z')]){const d=new Date(nextSchedule(n));const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Madrid',weekday:'short',hour:'2-digit',minute:'2-digit',hour12:false}).format(d);assert.match(parts,/Thu/);assert.match(parts,/10:30/);}});
test('dry-run never calls any Brevo endpoint',async()=>{let calls=0;const out=await execute({dir:fixture(),now:NOW,fetcher:async()=>{calls++;throw Error('not expected')}});assert.equal(calls,0);assert.equal(out.state,'LAB_DRY_RUN_NO_BREVO_CALLS');});
test('stale or wrong editorial week blocks',()=>{assert.throws(()=>validateEditorial({dir:fixture({date:'2026-11-10'}),now:NOW}),/HOLD_STALE/);assert.throws(()=>validateEditorial({dir:fixture({weekly_campaign_suffix:'2026w46'}),now:NOW}),/HOLD_WRONG_WEEK/);});
test('no release proof or switch keeps scheduling disabled',async()=>{let calls=0;await assert.rejects(()=>execute({dir:fixture(),now:NOW,mode:'schedule',key:'fake',fetcher:async()=>{calls++}}),/HOLD_LIVE_SWITCH_OFF/);assert.equal(calls,0);});
test('proof hash, marketing consent and free credits all gate',()=>{const p=approvedProof();const date=nextSchedule(NOW);assert.equal(validateRelease({...p,now:NOW,sendDate:date}).total,2);assert.throws(()=>validateRelease({...p,sha256:'invalid',now:NOW,sendDate:date}),/HASH/);const f=approvedProof({gates:{...p.release.gates,marketing_consent_evidence:false}});assert.throws(()=>validateRelease({...f,now:NOW,sendDate:date}),/MARKETING_CONSENT/);const c=approvedProof({available_daily_credits:1});assert.throws(()=>validateRelease({...c,now:NOW,sendDate:date}),/EXCEEDS_FREE_CREDITS/);});
test('no accidental live mode without explicit schedule flag',async()=>{const prior=process.env.NEWS001_SCHEDULE_ENABLED;process.env.NEWS001_SCHEDULE_ENABLED='false';try{await assert.rejects(()=>execute({dir:fixture(),now:NOW,mode:'schedule',key:'fake'}),/HOLD_LIVE_SWITCH_OFF/);}finally{if(prior===undefined)delete process.env.NEWS001_SCHEDULE_ENABLED;else process.env.NEWS001_SCHEDULE_ENABLED=prior;}});
test('existing week blocks all mutations before creating either campaign',async()=>{
 const dir=fixture(),p=approvedProof(),proof=join(dir,'proof.json');writeFileSync(proof,p.raw);let posts=0;const prior=process.env.NEWS001_SCHEDULE_ENABLED;process.env.NEWS001_SCHEDULE_ENABLED='true';try{
 await assert.rejects(()=>execute({dir,now:NOW,mode:'schedule',key:'dummy',releasePath:proof,releaseSha256:p.sha256,fetcher:async(url,options)=>{if(options.method==='POST')posts++;return{ok:true,json:async()=>({campaigns:[{name:'NEWS001-B2B-2026w47-CEREBRO-ORIGINAL-10',id:123}]})};}}),/HOLD_WEEK_ALREADY_EXISTS/);
 assert.equal(posts,0);
 }finally{if(prior===undefined)delete process.env.NEWS001_SCHEDULE_ENABLED;else process.env.NEWS001_SCHEDULE_ENABLED=prior;}
});
test('schedule requires both verified campaigns after creation',async()=>{
 const dir=fixture(),p=approvedProof(),proof=join(dir,'proof.json');writeFileSync(proof,p.raw);let id=100,posts=0;const saved={};const prior=process.env.NEWS001_SCHEDULE_ENABLED;process.env.NEWS001_SCHEDULE_ENABLED='true';try{
 const out=await execute({dir,now:NOW,mode:'schedule',key:'dummy',releasePath:proof,releaseSha256:p.sha256,fetcher:async(url,o)=>{
   if(o.method==='POST'){posts++;const v=JSON.parse(o.body);saved[++id]=v;return{ok:true,json:async()=>({id})};}
   if(url.includes('?type=classic'))return{ok:true,json:async()=>({campaigns:[]})};
   const found=saved[Number(url.split('/').at(-1))];return{ok:true,json:async()=>({name:found.name,status:'scheduled',recipients:{lists:found.recipients.listIds}})};
 }});
 assert.equal(posts,2);assert.equal(out.state,'TWO_WEEKLY_CAMPAIGNS_SCHEDULED_VERIFIED');assert.deepEqual(Object.values(saved).map(x=>x.recipients.listIds[0]),[18,17]);assert.ok(Object.values(saved).every(x=>'scheduledAt'in x&&!('sendNow'in x)));
 }finally{if(prior===undefined)delete process.env.NEWS001_SCHEDULE_ENABLED;else process.env.NEWS001_SCHEDULE_ENABLED=prior;}
});
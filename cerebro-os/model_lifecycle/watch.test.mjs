import test from 'node:test';
import assert from 'node:assert/strict';
import {POLICY,parseNotices,officialNoticeLinks,matchRetirements,SEED_REGISTRY,scan} from './watch.worker.mjs';
const source='https://developers.cloudflare.com/changelog/post/2026-11-05-planned-model-deprecations/';
const fixture=[
 '# Workers AI','## Recommended replacements','* '+String.fromCharCode(96)+'@cf/google/gemma-4-26b-a4b-it'+String.fromCharCode(96),
 '#### Models deprecated on November 20, 2026','#### LLMs',
 '* '+String.fromCharCode(96)+'@cf/meta/llama-3.1-8b-instruct-fp8'+String.fromCharCode(96),
 '* '+String.fromCharCode(96)+'@cf/qwen/qwq-32b'+String.fromCharCode(96),
 '#### Other models','* '+String.fromCharCode(96)+'@cf/openai/whisper-tiny-en'+String.fromCharCode(96),
 '## New section','* '+String.fromCharCode(96)+'@cf/not-in-scope/ignored'+String.fromCharCode(96)
].join('\n');
test('official dated section only; replacement does not count',()=>{
 const n=parseNotices(fixture,source);assert.equal(n.length,1);
 assert.equal(n[0].deprecated_on,'2026-11-20');assert.equal(n[0].model_ids.length,3);
 assert.ok(!n[0].model_ids.includes('@cf/google/gemma-4-26b-a4b-it'));
 assert.ok(!n[0].model_ids.includes('@cf/not-in-scope/ignored'));
});
test('source and malformed dates fail closed',()=>{
 assert.deepEqual(parseNotices(fixture,'https://malicious.example/changelog/post/model/'),[]);
 assert.deepEqual(parseNotices('#### Models deprecated on November 31, 2026\n* '+
   String.fromCharCode(96)+'@cf/example/model'+String.fromCharCode(96),source),[]);
});
test('RSS discovery filters to Cloudflare model deprecation URLs',()=>{
 assert.deepEqual(officialNoticeLinks('<link>'+source+'</link><link>https://evil.example/a</link><link>'+source+'</link>'),[source]);
});
test('exact match flags old model; replacement is not flagged',()=>{
 const before=[{company_id:'fenix-capital',engine_id:'SOC-IG',environment:'LAB',version:'0.1.0',worker:'ig-lab',
  models:[{role:'generator',model_id:'@cf/meta/llama-3.1-8b-instruct-fp8'}]}];
 const notice=parseNotices(fixture,source),now=new Date('2026-11-17T08:00:00Z');
 const events=matchRetirements(notice,before,now);assert.equal(events.length,1);
 assert.equal(events[0].state,'PATCH_REQUIRED_LAB');assert.equal(events[0].days_remaining,2);
 assert.equal(events[0].deploy_allowed,false);assert.equal(events[0].publish_allowed,false);
 assert.deepEqual(matchRetirements(notice,SEED_REGISTRY,now),[]);
});
test('invalid inventory and model references cannot be treated as green',()=>{
 assert.throws(()=>matchRetirements(parseNotices(fixture,source),
  [{company_id:'f',engine_id:'SOC',worker:'ig',version:'1.0.0',environment:'GLOBAL',models:[]}]),/INVENTORY_CONTRACT/);
 assert.throws(()=>matchRetirements([], [{...SEED_REGISTRY[0],models:[{role:'generator',model_id:'bad'}]}]),/MODEL_CONTRACT/);
});
test('private scan writes only KV evidence and triggers no paid inference',async()=>{
 const data={};const KV={async get(key){return data[key]||null},async put(key,val){data[key]=JSON.parse(val)}};
 const saved=globalThis.fetch;
 globalThis.fetch=async url=>({ok:true,text:async()=>String(url).endsWith('.xml')?'<link>'+source+'</link>':fixture});
 try{
  const r=await scan({LIFECYCLE_KV:KV,LAB_READONLY:'true',COMPANY_SCOPE:'GLOBAL'},new Date('2026-11-17T08:00:00Z'));
  assert.equal(r.state,'NO_KNOWN_MATCH');assert.equal(r.affected.length,0);
  assert.equal(r.model_calls,0);assert.equal(r.autonomous_promotion,false);
  assert.equal(data['model-lifecycle/v0/last-scan'].state,'NO_KNOWN_MATCH');
  assert.equal(POLICY.autonomous_promotion,false);
  await assert.rejects(scan({LIFECYCLE_KV:KV,LAB_READONLY:'false',COMPANY_SCOPE:'GLOBAL'}),/LAB_SCOPE_DENIED/);
 }finally{globalThis.fetch=saved;}
});

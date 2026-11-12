import test from 'node:test';
import assert from 'node:assert/strict';
import {CEREBROUniversalMediaClient,createUniversalMediaClient} from '../runtime/ums001_universal_media_client.mjs';
const token='f'.repeat(80);
const make=(out={})=>{const seen=[];const gateway={async universalImageFromRuntime(...args){seen.push(args);return typeof out==='function'?out(...args):out;}};const client=new CEREBROUniversalMediaClient({gateway,runtimeId:'SOCIAL-LAB',engineId:'SOC-001',runtimeToken:token});return {client,seen};};
test('one shared connection per runtime, scoped to issuer',async()=>{
  const {client,seen}=make({engine_id:'SOC-001',provider:'UMS-001',environment:'LAB',status:'READY_AUTHENTICATED',publish_authorized:false});
  const r=await client.capability();
  assert.equal(r.status,'READY_AUTHENTICATED');
  assert.deepEqual(seen[0],['SOCIAL-LAB','SOC-001','CAPABILITY',null,token]);
});
test('no fake ready for unregistered motor',async()=>{
  const {client}=make({engine_id:'SOC-001',provider:'UMS-001',environment:'LAB',status:'PENDING_FACTORY_IAM',publish_authorized:false});
  assert.equal((await client.capability()).status,'PENDING_FACTORY_IAM');
});
test('reject cross-company, production or missing secret',()=>{
 for(const opts of [{companyId:'other'},{environment:'PROD'},{runtimeToken:'short'}]){
  assert.throws(()=>new CEREBROUniversalMediaClient({gateway:{universalImageFromRuntime(){}},runtimeId:'SOCIAL-LAB',engineId:'SOC-001',runtimeToken:token,...opts}),/NOT_READY/);
 }
});
test('request forwards only a bounded private brief',async()=>{
 const id='UMS001-LAB-REPLAY-SOC-20261112-01';
 const {client,seen}=make({state:'ACCEPTED',engine_id:'SOC-001',request_id:id,environment:'LAB',publish_authorized:false});
 await client.request({request_id:id,prompt:'Original fictional Cordoba apartment interior, natural morning light, no branding.'});
 assert.equal(seen[0][2],'REQUEST');
 assert.deepEqual(Object.keys(seen[0][3]).sort(),['prompt','request_id']);
});
test('cannot claim a publish operation',async()=>{
 const {client}=make({state:'ACCEPTED',engine_id:'SOC-001',request_id:'UMS001-LAB-REPLAY-SOC-20261112-01',environment:'LAB',publish_authorized:true});
 await assert.rejects(client.request({request_id:'UMS001-LAB-REPLAY-SOC-20261112-01',prompt:'Original fictional Cordoba apartment interior, natural morning light, no branding.'}),/NOT_ACCEPTED/);
});
test('reject forged JPEG response',async()=>{
 const id='UMS001-LAB-REPLAY-SOC-20261112-01';
 const {client}=make({state:'PRIVATE_ASSET_RECEIVED',mime:'image/jpeg',engine_id:'SOC-001',request_id:id,sha256:'a'.repeat(64),publish_authorized:false,bytes:new Uint8Array(5000)});
 await assert.rejects(client.privateJPEG(id),/INVALID_JPEG/);
});
test('factory helper points to the one bound gateway',()=>{
 const client=createUniversalMediaClient({CEREBRO_MEDIA_GATEWAY:{universalImageFromRuntime(){}},CEREBRO_RUNTIME_TOKEN:token},{runtimeId:'SOCIAL-LAB',engineId:'SOC-001'});
 assert.equal(client.engineId,'SOC-001');
});
test('refuse extra publishing and budgeting controls from callers',async()=>{
 const {client}=make({state:'ACCEPTED',engine_id:'SOC-001',request_id:'UMS001-LAB-REPLAY-SOC-20261112-01',environment:'LAB',publish_authorized:false});
 await assert.rejects(client.request({request_id:'UMS001-LAB-REPLAY-SOC-20261112-01',prompt:'Original fictional Cordoba apartment interior, natural morning light, no branding.',publish_requested:true}),/SCHEMA_DENIED/);
});

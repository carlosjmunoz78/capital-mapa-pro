'use strict';
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const vm = require('node:vm');
const {createLabKnowledgeReader} = require('./gateway_sheets_lab.cjs');

const scope = {company_id:'test-a',department_id:'seo',engine_id:'SEO-LAB',
  agent_id:'A',subagent_id:'A.S',environment:'LAB',version:'v1'};
const values = {
  Config: [['key','value'], ...Object.entries({company_id:'test-a',environment:'LAB',engine_id:'KNOWLEDGE-FACTORY-001',
    prod_allowed:'FALSE',gateway_push_enabled:'FALSE',publication_enabled:'FALSE',certification_allowed:'FALSE',
    model_calls_enabled:'FALSE',external_actions_allowed:'FALSE'})],
  Departamentos: [[],['test-a','seo','SEO-LAB','LAB']],
  Agentes: [[],['test-a','SEO-LAB','LAB','A','Agent',1,'ROLE:A','','NOT_CERTIFIED','FALSE']],
  Especialistas: [[],['test-a','SEO-LAB','LAB','A.S','A','title','','OVERLAY:A.S','','','NOT_CERTIFIED','FALSE',0,'v1']],
  Asignaciones: [[...Array(10).fill(''),'engine_id','environment','department_id'],
    ['test-a','A.S','A','ROLE:A','OVERLAY:A.S','RULE:R','v1','STAGED_NOT_INJECTED','FALSE','','SEO-LAB','LAB','seo']],
  Biblioteca: [[], ...[['ROLE:A','ROLE'],['OVERLAY:A.S','SPECIALIST'],['RULE:R','RULE']]
    .map(([id,kind])=>[id,kind,'test-a','LAB','','v1','example-synthetic','{"value":1}','STAGED'])],
};
const sheet = {getSheetByName: name=>({getParent:()=>sheet,getDataRange:()=>({getValues:()=>values[name]})})};
const code = readFileSync(join(__dirname,'Code.gs'),'utf8');
const bundle = vm.runInNewContext(code + '\nconst index=cerebroIndex_(); cerebroResolve_(index,[...index.specialists.keys()][0])',
  {SpreadsheetApp:{getActiveSpreadsheet:()=>sheet}});
const digest = createHash('sha256').update(JSON.stringify(bundle)).digest('hex');
values.Entregas_LAB = [[],['date','test-a','LAB','A.S','RESOLVED_LAB',digest]];

const events = [];
let googleCalls = 0;
const reader = createLabKnowledgeReader({
  authenticate: context=>context==='trusted'?{id:'fixture-reader',grants:[scope]}:null,
  policyCheck: ()=>true,
  googleAccessToken: ()=>'fixture-token',
  audit: event=>events.push(event),
  fetchImpl: (url, opts)=>{
    googleCalls++;
    assert.equal(url.hostname,'sheets.googleapis.com');
    assert.equal(opts.method,'GET');
    return Promise.resolve({ok:true,json:async()=>({
      spreadsheetId:url.pathname.split('/')[3],
      valueRanges:url.searchParams.getAll('ranges').map(range=>({range,values:values[range.split('!')[0]]})),
    })});
  },
});
(async()=>{
  await assert.rejects(reader('anonymous',scope),/UNAUTHENTICATED_CONSUMER/);
  await assert.rejects(reader('trusted',{...scope,company_id:'test-b'}),/SCOPE_DENIED/);
  await assert.rejects(reader('trusted',{...scope,version:'v2'}),/SCOPE_DENIED/);
  assert.equal(googleCalls,0);
  const output=await reader('trusted',scope);
  assert.equal(output.sha256,digest);
  assert.equal(output.bundle.may_publish,false);
  assert.equal(output.bundle.items.length,3);
  assert.equal(events.at(-1).outcome,'READ_VERIFIED');
  values.Entregas_LAB[1][5]='wrong-hash';
  await assert.rejects(reader('trusted',scope),/DELIVERY_RECEIPT_PENDING/);
  assert.equal(events.at(-1).outcome,'FAILED');
  assert.ok(!JSON.stringify(events).includes('fixture-token'));
  console.log('PASS: authenticated scope, exact receipt hash, read-only I/O, no credential in audit');
})().catch(error=>{console.error(error);process.exitCode=1;});

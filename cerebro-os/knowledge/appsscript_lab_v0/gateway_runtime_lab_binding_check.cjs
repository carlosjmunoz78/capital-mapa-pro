'use strict';
const assert = require('node:assert/strict');
const {createHash} = require('node:crypto');
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const vm = require('node:vm');
const {
  SERVICE_ACCOUNT, CAPABILITY, CONNECTOR_ID,
  createLabGatewayKnowledgeCapability,
  createGoogleManagedReaderTokenProvider,
} = require('./gateway_runtime_lab_binding.cjs');

const company_id = 'fenix-capital';
const input = [
  {company_id, department_id:'facebook', engine_id:'SOC-FB-FINANCIAL-REAL-ESTATE-V1',agent_id:'FB-00',subagent_id:'FB-00.SA-001',environment:'LAB',version:'2026-11-18.v1'},
  {company_id, department_id:'instagram',engine_id:'SOC-001/SOCBOOT-001',agent_id:'IG-00',subagent_id:'IG-00.SA-001',environment:'LAB',version:'1.0.0-candidate'},
  {company_id, department_id:'linkedin',engine_id:'SOC-LI-FINANCIAL-REAL-ESTATE-V1',agent_id:'LI-00',subagent_id:'LI-00.SA-001',environment:'LAB',version:'0.1.0'},
];
const cfg = {company_id,environment:'LAB',engine_id:'KNOWLEDGE-FACTORY-001',prod_allowed:'FALSE',gateway_push_enabled:'FALSE',publication_enabled:'FALSE',certification_allowed:'FALSE',model_calls_enabled:'FALSE',external_actions_allowed:'FALSE'};
const values = {
  Config: [['clave','valor'],...Object.entries(cfg)],
  Departamentos: [['company_id','department_id','engine_id','environment']],
  Agentes: [['company_id','engine_id','environment','agent_id']],
  Especialistas: [['company_id','engine_id','environment','component_id']],
  Asignaciones: [[...Array(10).fill(''),'engine_id','environment','department_id']],
  Biblioteca: [['knowledge_id','tipo','company_id']],
};
for(const s of input) {
  const rule = 'RULE:' + s.department_id;
  const role = 'ROLE:' + s.agent_id;
  const overlay = 'OVERLAY:' + s.subagent_id;
  values.Departamentos.push([s.company_id,s.department_id,s.engine_id,s.environment]);
  values.Agentes.push([s.company_id,s.engine_id,'LAB',s.agent_id,'Test role',1,role,'','NOT_CERTIFIED','FALSE']);
  values.Especialistas.push([s.company_id,s.engine_id,'LAB',s.subagent_id,s.agent_id,'Test specialty','',overlay,'','','NOT_CERTIFIED','FALSE',0,s.version]);
  values.Asignaciones.push([s.company_id,s.subagent_id,s.agent_id,role,overlay,rule,s.version,'STAGED_NOT_INJECTED','FALSE','',s.engine_id,'LAB',s.department_id]);
  for(const [ref,kind]of [[role,'ROLE'],[overlay,'SPECIALIST'],[rule,'RULE']])values.Biblioteca.push([ref,kind,s.company_id,'LAB','',s.version,'synthetic-test-source',JSON.stringify({name:ref}),'TEST_NOT_CERTIFIED']);
}
const sheet = {getSheetByName(name) {return {getParent:()=>sheet,getDataRange:()=>({getValues:()=>values[name]})};}};
const code = readFileSync(join(__dirname,'Code.gs'),'utf8');
const now = '2026-11-19T11:00:00.000Z';
values.Entregas_LAB = [['fecha_utc','company_id','environment','component_id','estado','bundle_sha256']];
for(const request of input){
  const bundle = vm.runInNewContext(code + '\nconst idx = cerebroIndex_(); const key=cerebroKey_(cerebroKey_(request.company_id,request.engine_id,request.environment),request.subagent_id); cerebroResolve_(idx,key)', {SpreadsheetApp:{getActiveSpreadsheet:()=>sheet},request});
  const hash=createHash('sha256').update(JSON.stringify(bundle)).digest('hex');
  values.Entregas_LAB.push([now,request.company_id,'LAB',request.subagent_id,'RESOLVED_LAB',hash]);
}
const caller=Symbol('verified-runtime-internal-boundary');
const principal={verified:true,id:'cerebro-forge-reader-runtime',environment:'LAB',service_account_email:SERVICE_ACCOUNT};
let calls=0;
const audit=[];
const opts={
  enabled: true,
  authenticateRuntime: ctx=>ctx===caller?principal:null,
  readTrustedGrants: p=>p===principal?input:[],
  routeGateway: req=>({status:'ROUTED',connector_id:CONNECTOR_ID,company_id:req.company_id,engine_id:req.engine_id,environment:req.environment,version:req.version}),
  policyCheck: ()=>true,
  googleAccessToken: args=>args.service_account_email===SERVICE_ACCOUNT?'PRIVATE_TEST_TOKEN':null,
  persistAudit: event=>audit.push(event),
  fetchImpl: async(url,options)=>{
    calls++;
    assert.equal(url.hostname,'sheets.googleapis.com');
    assert.equal(options.method,'GET');
    assert.equal(options.headers.Authorization,'Bearer PRIVATE_TEST_TOKEN');
    return {ok:true,json:async()=>({spreadsheetId:url.pathname.split('/')[3],valueRanges:url.searchParams.getAll('ranges').map(range=>({range,values:values[range.split('!')[0]]}))})};
  },
};
const reader=createLabGatewayKnowledgeCapability(opts);
(async()=>{
  assert.equal(reader.capability,CAPABILITY);
  assert.equal(createLabGatewayKnowledgeCapability({...opts,enabled:false}).status,'DISABLED_LAB');
  await assert.rejects(createLabGatewayKnowledgeCapability({...opts,enabled:false}).read(caller,input[0]),/DISABLED/);
  assert.equal(typeof reader.read,'function');
  await assert.rejects(reader.read({},input[0]),/GATEWAY_LAB_RUNTIME_IDENTITY_NOT_VERIFIED/);
  await assert.rejects(reader.read(caller,{...input[0],company_id:'other-company'}),/SCOPE_DENIED/);
  await assert.rejects(reader.read(caller,{...input[0],version:'v2'}),/SCOPE_DENIED/);
  await assert.rejects(reader.read(caller,{...input[0],environment:'PROD'}),/INVALID_LAB_SCOPE/);
  assert.equal(calls,0,'denials must not reach Google');
  for(const request of input){
    const result=await reader.read(caller,request);
    assert.equal(result.bundle.subagent_id,request.subagent_id);
    assert.equal(result.bundle.environment,'LAB');
    assert.equal(result.bundle.certification_status,'NOT_CERTIFIED');
    assert.equal(result.bundle.items.length,3);
    assert.equal(result.sha256,values.Entregas_LAB.find(x=>x[3]===request.subagent_id)[5]);
  }
  assert.equal(calls,3);
  assert.ok(audit.filter(x=>x.outcome==='READ_VERIFIED').length===3);
  assert.ok(!JSON.stringify(audit).includes('PRIVATE_TEST_TOKEN'));
  values.Entregas_LAB[3][5]='corrupted_hash';
  await assert.rejects(reader.read(caller,input[2]),/DELIVERY_RECEIPT_PENDING/);
  assert.equal(audit.at(-1).outcome,'FAILED');
  assert.equal(calls,4);
  const wrong = createLabGatewayKnowledgeCapability({...opts,routeGateway:req=>({...opts.routeGateway(req),connector_id:'wrong'})});
  await assert.rejects(wrong.read(caller,input[0]),/SCOPE_DENIED/);
  assert.equal(calls,4);
  const noAudit = createLabGatewayKnowledgeCapability({...opts,persistAudit:()=>{throw Error('AUDIT_UNAVAILABLE')}});
  await assert.rejects(noAudit.read(caller,input[0]),/AUDIT_UNAVAILABLE/);
  const notVerified = createLabGatewayKnowledgeCapability({...opts,authenticateRuntime:()=>({...principal,service_account_email:'other@company'})});
  await assert.rejects(notVerified.read(caller,input[0]),/GATEWAY_LAB_RUNTIME_IDENTITY_NOT_VERIFIED/);
  const scoped = createLabGatewayKnowledgeCapability({...opts,policyCheck:()=>false});
  await assert.rejects(scoped.read(caller,input[0]),/SCOPE_DENIED/);
  let metaCalls=[];
  const tokenProvider=createGoogleManagedReaderTokenProvider({fetchImpl:async(url,p)=>{
    metaCalls.push(url);
    assert.equal(p.headers['Metadata-Flavor'],'Google');
    if(url.endsWith('/email'))return {ok:true,text:async()=>SERVICE_ACCOUNT};
    if(url.endsWith('/token'))return {ok:true,json:async()=>({token_type:'Bearer',access_token:'EPHEMERAL',expires_in:600})};
    throw Error('UNEXPECTED_META_URL');
  }});
  assert.equal(await tokenProvider({service_account_email:SERVICE_ACCOUNT,environment:'LAB'}),'EPHEMERAL');
  assert.equal(await tokenProvider({service_account_email:SERVICE_ACCOUNT,environment:'LAB'}),'EPHEMERAL');
  assert.equal(metaCalls.filter(x=>x.endsWith('/email')).length,1);
  await assert.rejects(tokenProvider({service_account_email:SERVICE_ACCOUNT,environment:'PROD'}),/GOOGLE_READER_SCOPE_DENIED/);
  await assert.rejects(createGoogleManagedReaderTokenProvider({fetchImpl:async()=>({ok:true,text:async()=> 'unauthorized@other.test'})})({service_account_email:SERVICE_ACCOUNT,environment:'LAB'}),/GOOGLE_MANAGED_SERVICE_ACCOUNT_MISMATCH/);
  console.log('PASS: 3 synthetic lab reads, 5+ deny gates, no Google on denied scopes, hash check, audit fail-closed, no secrets, metadata identity enforcement');
})().catch(error=>{console.error(error);process.exitCode=1});
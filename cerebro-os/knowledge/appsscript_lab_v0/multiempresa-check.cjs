const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const engine = 'SOC-FB-FINANCIAL-REAL-ESTATE-V1';
const scope = [
  ['fenix-capital', 'facebook', engine],
  ['fenix-capital', 'seo', 'SEO-LAB'],
  ['lab-tenant-2', 'linkedin', 'LINKEDIN-LAB'],
];
const cfg = Object.entries({company_id:'fenix-capital', environment:'LAB', engine_id:'KNOWLEDGE-FACTORY-001', prod_allowed:'FALSE', gateway_push_enabled:'FALSE', publication_enabled:'FALSE', certification_allowed:'FALSE', model_calls_enabled:'FALSE', external_actions_allowed:'FALSE'});
const rows = {
  Config: [['key','value'], ...cfg],
  Departamentos: [['company_id','department_id','engine_id','environment'], ...scope.map(([c,d,e])=>[c,d,e,'LAB'])],
  Agentes: [[], ...scope.map(([c,d,e])=>[c,e,'LAB','A','Agent',1,'ROLE:A','','NOT_CERTIFIED','FALSE'])],
  Especialistas: [[], ...scope.map(([c,d,e])=>[c,e,'LAB','A.S','A',d,'','OVERLAY:A.S','','','NOT_CERTIFIED','FALSE',0,'v1'])],
  Asignaciones: [[...Array(10).fill(''), 'engine_id','environment','department_id'], ...scope.map(([c,d,e],i)=>[c,'A.S','A','ROLE:A','OVERLAY:A.S','RULE:R','v1','STAGED_NOT_INJECTED','FALSE','',...(i?[e,'LAB',d]:[])])],
  Biblioteca: [[], ...['fenix-capital','lab-tenant-2'].flatMap(c=>[['ROLE:A','ROLE'],['OVERLAY:A.S','SPECIALIST'],['RULE:R','RULE']].map(([id,kind])=>[id,kind,c,'LAB','','v1',`source:${c}`,JSON.stringify({tenant:c}),'STAGED']))],
};
const book = {getSheetByName: name=> rows[name] ? {getParent:()=>book,getDataRange:()=>({getValues:()=>rows[name]})} : null};
const filename = process.argv[2] || require('node:path').join(__dirname,'Code.gs');
const context = vm.createContext({SpreadsheetApp:{getActiveSpreadsheet:()=>book}});
vm.runInContext(fs.readFileSync(filename,'utf8'),context);
const results = vm.runInContext('const ix=cerebroIndex_(); [...ix.specialists.keys()].map(k=>cerebroResolve_(ix,k))',context);
assert.deepEqual(Array.from(results, b=>b.department_id), ['facebook','seo','linkedin']);
assert.equal(new Set(Array.from(results, b=>b.subagent_id)).size,1);
assert.ok(results.every(b=>b.items.every(item=>item.payload.tenant===b.company_id) && b.certification_status==='NOT_CERTIFIED'));
rows.Biblioteca.splice(rows.Biblioteca.findIndex(x=>x[0]==='RULE:R'&&x[2]==='lab-tenant-2'),1);
assert.throws(()=>vm.runInContext('const missing=cerebroIndex_(); cerebroResolve_(missing,[...missing.specialists.keys()][2])',context),/KNOWLEDGE_MISSING:RULE:R/);
console.log('PASS: two tenants, three departments, identical IDs isolated; missing tenant rule fails closed');

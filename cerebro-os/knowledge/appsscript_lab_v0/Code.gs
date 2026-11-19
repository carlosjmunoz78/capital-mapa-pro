/** @OnlyCurrentDoc */
// CEREBRO OS · KNOWLEDGE-FACTORY-001 · UNIVERSAL LAB
const KFA = Object.freeze({
  company: 'fenix-capital', engine: 'KNOWLEDGE-FACTORY-001', environment: 'LAB',
  sourceEngine: 'SOC-FB-FINANCIAL-REAL-ESTATE-V1',
  sheets: {departments:'Departamentos', agents:'Agentes', config:'Config', specialists:'Especialistas', library:'Biblioteca', assignments:'Asignaciones', deliveries:'Entregas_LAB', audit:'Auditoria', pilot:'Piloto'},
  cursorKey: 'KFA_LAB_CURSOR_20261119', maxBatch: 50, runLimitMs: 250000
});

function onOpen() {
  SpreadsheetApp.getUi().createMenu('CEREBRO · LAB')
    .addItem('Validar especialistas LAB', 'cerebroLabValidateAll')
    .addItem('Ejecutar piloto LAB', 'cerebroLabPilot')
    .addItem('Procesar siguiente lote LAB', 'cerebroLabRunBatch')
    .addItem('Encolar cambios de conocimiento LAB', 'cerebroLabQueueIncremental')
    .addToUi();
}

function cerebroSheet_(name) {
  const file = SpreadsheetApp.getActiveSpreadsheet();
  if (!file) throw Error('NOT_A_BOUND_SHEET');
  const sheet = file.getSheetByName(name);
  if (!sheet) throw Error('MISSING_SHEET:' + name);
  return sheet;
}
function cerebroSnapshot_(sheetName) {
  const all = cerebroSheet_(sheetName).getDataRange().getValues();
  if (!all.length) throw Error('EMPTY_SHEET:' + sheetName);
  return all;
}
function cerebroConfig_() {
  const a = cerebroSnapshot_(KFA.sheets.config), config = Object.create(null);
  for (let i=1;i<a.length;i++) if (String(a[i][0]).trim()) config[String(a[i][0]).trim()] = String(a[i][1]);
  if (!config.company_id || config.environment !== 'LAB' ||
      config.engine_id !== KFA.engine || config.prod_allowed !== 'FALSE' ||
      config.gateway_push_enabled !== 'FALSE' || config.publication_enabled !== 'FALSE' ||
      config.certification_allowed !== 'FALSE' || config.model_calls_enabled !== 'FALSE' ||
      config.external_actions_allowed !== 'FALSE') throw Error('BLOCKED_UNSAFE_CONFIG');
  return config;
}
function cerebroKey_(...parts) {
  return JSON.stringify(parts.map(String));
}
function cerebroIndex_() {
  const cfg=cerebroConfig_();
  const departments=new Map(), agents=new Map(), specialists=new Map(), mapping=new Map(), library=new Map();
  const legacy=[cfg.company_id,KFA.sourceEngine,'LAB'];
  const legacyKey=cerebroKey_(...legacy);
  const registered=cerebroSheet_(KFA.sheets.config).getParent().getSheetByName(KFA.sheets.departments);
  const departmentRows=registered ? registered.getDataRange().getValues().slice(1) : [];
  departments.set(legacyKey,'facebook');
  for(const [company,department,engine,environment] of departmentRows) {
    if (![company,department,engine,environment].some(Boolean)) continue;
    if (!company || !department || !engine || environment!=='LAB') throw Error('INVALID_DEPARTMENT');
    const key=cerebroKey_(company,engine,environment);
    if (departments.has(key) && departments.get(key)!==department) throw Error('DEPARTMENT_CONFLICT');
    departments.set(key,department);
  }
  for(const r of cerebroSnapshot_(KFA.sheets.agents).slice(1)) {
    const scope=cerebroKey_(r[0],r[1],r[2]), key=cerebroKey_(scope,r[3]);
    if (!departments.has(scope) || !r[3] || agents.has(key) || r[8]!=='NOT_CERTIFIED' || String(r[9])!=='FALSE') throw Error('UNSAFE_AGENT:'+r[3]);
    agents.set(key,r);
  }
  for(const r of cerebroSnapshot_(KFA.sheets.specialists).slice(1)) {
    const scope=cerebroKey_(r[0],r[1],r[2]), key=cerebroKey_(scope,r[3]);
    if (!r[3] || specialists.has(key) || !agents.has(cerebroKey_(scope,r[4])) || !r[13] || r[10]!=='NOT_CERTIFIED' || String(r[11])!=='FALSE') throw Error('UNSAFE_SPECIALIST:'+r[3]);
    specialists.set(key,r);
  }
  const rows=cerebroSnapshot_(KFA.sheets.assignments);
  const fields=['engine_id','environment','department_id'].map(name=>rows[0].indexOf(name));
  for(const r of rows.slice(1)) {
    const [engine,environment,department]=fields.map(i=>i<0?'':r[i]);
    const hasScope=Boolean(engine||environment||department);
    const scope=hasScope?cerebroKey_(r[0],engine,environment):legacyKey;
    const key=cerebroKey_(scope,r[1]);
    if (!specialists.has(key) || mapping.has(key) || (hasScope? !department || departments.get(scope)!==department : r[0]!==cfg.company_id) || !r[6] || r[7]!=='STAGED_NOT_INJECTED' || String(r[8])!=='FALSE') throw Error('UNSAFE_MAPPING:'+r[1]);
    mapping.set(key,r);
  }
  const tenants=new Set([...departments.keys()].map(key=>JSON.parse(key)[0]));
  for(const r of cerebroSnapshot_(KFA.sheets.library).slice(1)) {
    const key=cerebroKey_(r[2],r[3],r[0],r[5]);
    if (!r[0] || !r[5] || !r[6] || library.has(key) || !tenants.has(r[2]) || r[3]!=='LAB' || /^(CERTIFIED|PROD)$/.test(r[8])) throw Error('UNSAFE_KNOWLEDGE:'+r[0]);
    library.set(key,r);
  }
  if (!specialists.size || specialists.size!==mapping.size) throw Error('INVENTORY_DRIFT');
  return {cfg,departments,agents,specialists,mapping,library};
}
function cerebroResolve_(idx,key) {
  const row=idx.specialists.get(key), map=idx.mapping.get(key);
  if (!row || !map || row[0]!==map[0] || row[4]!==map[2]) throw Error('SPECIALIST_MAPPING_NOT_FOUND');
  const [company,engine,environment,componentId,agentId]=row;
  const department=idx.departments.get(cerebroKey_(company,engine,environment));
  const agent=idx.agents.get(cerebroKey_(cerebroKey_(company,engine,environment),agentId));
  if (map[3]!==agent[6] || map[4]!==row[7]) throw Error('INVALID_OVERLAY_REFERENCE:'+componentId);
  const refs=[...new Set([map[3],map[4],...String(map[5]).split('|').filter(Boolean)])];
  const items=refs.map(ref=>{
    const [id,version=map[6]]=String(ref).split('@');
    const item=idx.library.get(cerebroKey_(company,environment,id,version));
    if (!item) throw Error('KNOWLEDGE_MISSING:'+ref);
    const payload=JSON.parse(String(item[7]));
    if (!payload || typeof payload!=='object') throw Error('INVALID_KNOWLEDGE_PAYLOAD:'+ref);
    return {knowledge_id:id,kind:item[1],version:item[5],knowledge_status:item[8],source_provenance:item[6],source_url:item[9]||'',payload};
  });
  if (items[0]?.kind!=='ROLE' || items[1]?.kind!=='SPECIALIST' || !items.some(x=>x.kind==='RULE')) throw Error('INCOMPLETE_KNOWLEDGE_BUNDLE:'+componentId);
  return {schema:'CEREBRO-KNOWLEDGE-BUNDLE-V0',company_id:company,department_id:department,
    agent_id:agentId,subagent_id:componentId,component_id:componentId,engine_id:engine,environment,
    version:String(row[13]),knowledge_pack_id:String(map[6]),knowledge_status:'RESOLVED_LAB',
    certification_status:'NOT_CERTIFIED',knowledge_refs:refs,items,consumer_verified:false,certified:false,
    may_publish:false,may_spend:false,may_write_crm:false,may_send_message:false,external_actions:0};
}

function cerebroHash_(value) {
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,
    JSON.stringify(value), Utilities.Charset.UTF_8);
  return bytes.map(x=>(x<0?x+256:x).toString(16).padStart(2,'0')).join('');
}
function cerebroAppend_(sheetName, rows) {
  if(!rows.length) return;
  const sh=cerebroSheet_(sheetName);
  sh.getRange(sh.getLastRow()+1,1,rows.length,rows[0].length).setValues(rows);
}
function cerebroLabValidateAll() {
  const idx=cerebroIndex_();
  for(const key of idx.specialists.keys()) cerebroResolve_(idx,key);
  const receipt={status:'LAB_BUNDLE_RESOLUTION_PASS',agents:idx.agents.size,total:idx.specialists.size,agent_consumed:0,certified:0};
  cerebroAppend_(KFA.sheets.audit,[[new Date().toISOString(),'APPS_SCRIPT','VALIDATE_ALL','LAB',receipt.total,'PASS',JSON.stringify(receipt)]]);
  console.log(JSON.stringify(receipt));
  return receipt;
}
function cerebroLabPilot() {
  const idx=cerebroIndex_(), key=idx.specialists.keys().next().value, b=cerebroResolve_(idx,key);
  const hash=cerebroHash_(b), now=new Date().toISOString();
  cerebroAppend_(KFA.sheets.pilot,[[now,b.company_id,b.subagent_id,'RESOLVED_LAB',b.knowledge_refs.join('|'),hash,'NO_REAL_AGENT_CONSUMPTION']]);
  const receipt={status:'RESOLVED_LAB',subagent_id:b.subagent_id,items:b.items.length,sha256:hash,agent_consumed:0,certified:0};
  console.log(JSON.stringify(receipt));
  return receipt;
}
function cerebroLabRunBatch() {
  const lock=LockService.getScriptLock();
  if (!lock.tryLock(3000)) throw Error('LAB_ALREADY_RUNNING');
  try {
    const started=Date.now(), idx=cerebroIndex_();
    if (idx.cfg.run_enabled!=='TRUE') throw Error('LAB_RUN_DISABLED');
    const max=Math.min(KFA.maxBatch,Math.max(1,parseInt(idx.cfg.max_batch,10)||25));
    const daily=Math.min(600,Math.max(1,parseInt(idx.cfg.max_daily_rows,10)||600));
    const now=new Date().toISOString(), history=cerebroSnapshot_(KFA.sheets.deliveries).slice(1);
    const seen=new Set(history.map(r=>cerebroKey_(r[1],r[2],r[3],r[5])));
    const used=history.filter(r=>String(r[0]).slice(0,10)===now.slice(0,10)).length;
    const rows=[];
    let current=0;
    for(const key of idx.specialists.keys()) {
      if (Date.now()-started>=KFA.runLimitMs) break;
      const b=cerebroResolve_(idx,key), hash=cerebroHash_(b);
      if (seen.has(cerebroKey_(b.company_id,b.environment,b.subagent_id,hash))) {current++;continue;}
      if (rows.length>=max || used+rows.length>=daily) continue;
      rows.push([now,b.company_id,b.environment,b.subagent_id,'RESOLVED_LAB',hash,b.items.filter(x=>x.kind==='RULE').length,1,1,0,'FALSE',JSON.stringify({department_id:b.department_id,engine_id:b.engine_id,agent_id:b.agent_id,version:b.version,knowledge_pack_id:b.knowledge_pack_id})]);
    }
    cerebroAppend_(KFA.sheets.deliveries,rows);
    SpreadsheetApp.flush();
    const total=current+rows.length;
    const receipt={status:total===idx.specialists.size?'LAB_PREVIEW_COMPLETE_NOT_INJECTED':'LAB_PREVIEW_PARTIAL',processed_now:rows.length,processed_total:total,total:idx.specialists.size,agent_consumed:0,certified:0};
    if (rows.length) cerebroAppend_(KFA.sheets.audit,[[now,'APPS_SCRIPT','BATCH_PREVIEW','LAB',rows.length,'PASS',JSON.stringify(receipt)]]);
    console.log(JSON.stringify(receipt));
    return receipt;
  } finally {lock.releaseLock();}
}
function cerebroLabInstallTimedBatch() {
  const cfg=cerebroConfig_();
  if (cfg.auto_trigger_enabled!=='TRUE'||cfg.run_enabled!=='TRUE')throw Error('TRIGGER_NOT_AUTHORIZED_IN_CONFIG');
  const existing=ScriptApp.getProjectTriggers().filter(x=>x.getHandlerFunction()==='cerebroLabRunBatch');
  if (existing.length) return {status:'ALREADY_INSTALLED',triggers:existing.length};
  ScriptApp.newTrigger('cerebroLabRunBatch').timeBased().everyMinutes(15).create();
  return {status:'LAB_TRIGGER_INSTALLED',prod_authorized:false};
}
function cerebroLabRemoveTimedBatch() {
  const toRemove=ScriptApp.getProjectTriggers().filter(x=>x.getHandlerFunction()==='cerebroLabRunBatch');
  toRemove.forEach(x=>ScriptApp.deleteTrigger(x));
  return {status:'LAB_TRIGGER_REMOVED',count:toRemove.length};
}


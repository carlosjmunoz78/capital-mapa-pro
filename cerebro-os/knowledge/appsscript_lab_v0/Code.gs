/**
 * CEREBRO OS · KNOWLEDGE-FACTORY-001 · LAB V0 (Google Sheets-bound Apps Script)
 * company_id=fenix-capital · environment=LAB · version=2026-11-19
 *
 * No HTTP endpoint, no UrlFetchApp, no AI, no Meta/CRM, no production writes.
 * A resolved bundle is NOT proof that an active agent consumed its knowledge.
 * Install into the NEW isolated CEREBRO knowledge spreadsheet only.
 */
const KFA = Object.freeze({
  company: 'fenix-capital', engine: 'KNOWLEDGE-FACTORY-001', environment: 'LAB',
  sourceEngine: 'SOC-FB-FINANCIAL-REAL-ESTATE-V1',
  sheets: {config:'Config', specialists:'Especialistas', library:'Biblioteca', assignments:'Asignaciones', deliveries:'Entregas_LAB', audit:'Auditoria', pilot:'Piloto'},
  cursorKey: 'KFA_LAB_CURSOR_20261119', maxBatch: 50, runLimitMs: 250000
});

function onOpen() {
  SpreadsheetApp.getUi().createMenu('CEREBRO · LAB')
    .addItem('Validar 527 especialistas (solo lectura)', 'cerebroLabValidateAll')
    .addItem('Previsualizar FB-00.SA-001', 'cerebroLabPilot')
    .addItem('Procesar siguiente lote LAB', 'cerebroLabRunBatch')
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
  if (config.company_id !== KFA.company || config.environment !== 'LAB' ||
      config.engine_id !== KFA.engine || config.prod_allowed !== 'FALSE' ||
      config.gateway_push_enabled !== 'FALSE' || config.publication_enabled !== 'FALSE' ||
      config.certification_allowed !== 'FALSE' || config.model_calls_enabled !== 'FALSE' ||
      config.external_actions_allowed !== 'FALSE') throw Error('BLOCKED_UNSAFE_CONFIG');
  return config;
}
function cerebroIndex_() {
  const cfg = cerebroConfig_();
  const s = cerebroSnapshot_(KFA.sheets.specialists), a = cerebroSnapshot_(KFA.sheets.assignments), l = cerebroSnapshot_(KFA.sheets.library);
  const specialists = new Map(), mapping = new Map(), library = new Map();
  for(let i=1;i<s.length;i++) {
    const r=s[i], id=String(r[3]);
    if (!id || specialists.has(id)) throw Error('DUPLICATE_SPECIALIST:' + id);
    if (r[0] !== KFA.company || r[2] !== 'LAB' || r[10] !== 'NOT_CERTIFIED' || String(r[11]) !== 'FALSE') throw Error('UNSAFE_SPECIALIST:' + id);
    specialists.set(id,r);
  }
  for(let i=1;i<a.length;i++) {
    const r=a[i], id=String(r[1]);
    if (!id || mapping.has(id)) throw Error('DUPLICATE_MAPPING:' + id);
    if (r[0] !== KFA.company || r[7] !== 'STAGED_NOT_INJECTED' || String(r[8]) !== 'FALSE') throw Error('UNSAFE_MAPPING:' + id);
    mapping.set(id,r);
  }
  for(let i=1;i<l.length;i++) {
    const r=l[i], id=String(r[0]);
    if (!id || library.has(id)) throw Error('DUPLICATE_KNOWLEDGE:' + id);
    if (r[2] !== KFA.company || r[3] !== 'LAB') throw Error('CROSS_TENANT_LIBRARY:' + id);
    if (r[8] === 'CERTIFIED' || r[8] === 'PROD') throw Error('UNSAFE_KNOWLEDGE_STATE:' + id);
    library.set(id,r);
  }
  if (specialists.size !== 527 || mapping.size !== 527 || library.size !== 595) throw Error('INVENTORY_DRIFT');
  return {cfg,specialists,mapping,library};
}

function cerebroResolve_(idx, componentId) {
  if (!/^FB-[A-Z0-9_\-]+\.SA-\d{3}$/.test(componentId)) throw Error('BAD_SPECIALIST_ID');
  const row=idx.specialists.get(componentId), map=idx.mapping.get(componentId);
  if (!row || !map || row[4] !== map[2]) throw Error('SPECIALIST_MAPPING_NOT_FOUND:' + componentId);
  if (map[3] !== 'ROLE:' + row[4] || map[4] !== 'OVERLAY:' + componentId) throw Error('INVALID_OVERLAY_REFERENCE:' + componentId);
  const keys=[...new Set([map[3],map[4], ...String(map[5]).split('|').filter(Boolean)])];
  const items=keys.map(id=>{
    const r=idx.library.get(id);
    if (!r || r[2] !== KFA.company || r[3] !== 'LAB') throw Error('KNOWLEDGE_MISSING:' + id);
    let payload;
    try { payload=JSON.parse(String(r[7])); } catch(_e){ throw Error('INVALID_KNOWLEDGE_JSON:' + id); }
    if (!payload || typeof payload !== 'object') throw Error('INVALID_KNOWLEDGE_PAYLOAD:' + id);
    return {knowledge_id:id, kind:r[1], version:r[5], status:r[8], payload:payload};
  });
  const roleCount=items.filter(x=>x.kind==='ROLE').length;
  const overlayCount=items.filter(x=>x.kind==='SPECIALIST').length;
  if (roleCount !== 1 || overlayCount !== 1 || items.filter(x=>x.kind==='RULE').length < 1) throw Error('INCOMPLETE_KNOWLEDGE_BUNDLE:' + componentId);
  return {schema:'CEREBRO-KNOWLEDGE-BUNDLE-V0',company_id:KFA.company,
    engine_id:KFA.sourceEngine,environment:'LAB',component_id:componentId,
    pack_id:String(map[6]),knowledge_refs:keys,items,
    training_state:'STAGED_NOT_INJECTED',consumer_verified:false,certified:false,
    may_publish:false,may_spend:false,may_write_crm:false,may_send_message:false,
    external_actions:0};
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
  const start=Date.now(),idx=cerebroIndex_();let ok=0;
  for(const id of idx.specialists.keys()) {cerebroResolve_(idx,id);ok++;}
  const receipt={status:'LAB_BUNDLE_RESOLUTION_PASS',total:ok,missing:527-ok,
    agent_consumed:0,professionally_certified:0,gateway_connected:false,elapsed_ms:Date.now()-start};
  cerebroAppend_(KFA.sheets.audit,[[new Date().toISOString(),'APPS_SCRIPT','VALIDATE_ALL','LAB',ok,'PASS','NO_EXTERNAL_ACTIONS']]);
  return receipt;
}
function cerebroLabPilot() {
  const idx=cerebroIndex_(),id='FB-00.SA-001',b=cerebroResolve_(idx,id);
  const hash=cerebroHash_(b),now=new Date().toISOString();
  cerebroAppend_(KFA.sheets.pilot,[[now,KFA.company,id,'READY_FOR_GATEWAY_PILOT',b.knowledge_refs.join('|'),hash,'SHADOW; NO REAL AGENT CONSUMPTION']]);
  return {component_id:id,status:'READY_FOR_GATEWAY_PILOT',knowledge_items:b.items.length,
    bundle_sha256:hash,agent_consumed:false,certified:false};
}
function cerebroLabRunBatch() {
  const lock=LockService.getScriptLock();
  if (!lock.tryLock(3000)) throw Error('LAB_ALREADY_RUNNING');
  try {
    const started=Date.now(),idx=cerebroIndex_();
    if(idx.cfg.run_enabled!=='TRUE')throw Error('LAB_RUN_DISABLED');
    const max=Math.min(KFA.maxBatch,Math.max(1,parseInt(idx.cfg.max_batch,10)||25));
    const ids=Array.from(idx.specialists.keys());
    const properties=PropertiesService.getScriptProperties();
    let cursor=Number(properties.getProperty(KFA.cursorKey)||0);
    if(!Number.isSafeInteger(cursor)||cursor<0||cursor>ids.length)throw Error('CURSOR_INVALID');
    const result=[],now=new Date().toISOString();
    while(cursor<ids.length&&result.length<max&&Date.now()-started<KFA.runLimitMs){
      const b=cerebroResolve_(idx,ids[cursor]);
      result.push([now,KFA.company,'LAB',b.component_id,'READY_FOR_GATEWAY_PILOT',
        cerebroHash_(b),b.items.filter(x=>x.kind==='RULE').length,1,1,0,'FALSE',
        'PREVIEW ONLY: agent has NOT consumed knowledge']);
      cursor++;
    }
    cerebroAppend_(KFA.sheets.deliveries,result);
    properties.setProperty(KFA.cursorKey,String(cursor));
    cerebroAppend_(KFA.sheets.audit,[[now,'APPS_SCRIPT','BATCH_PREVIEW','LAB',result.length,'PASS','CURSOR '+cursor+'/527; NO_GATEWAY_PUSH']]);
    return {status:cursor===ids.length?'LAB_PREVIEW_COMPLETE_NOT_INJECTED':'LAB_PREVIEW_PARTIAL',
      processed_now:result.length,processed_total:cursor,total:ids.length,
      agent_consumed:0,professionally_certified:0,prod_authorized:false};
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


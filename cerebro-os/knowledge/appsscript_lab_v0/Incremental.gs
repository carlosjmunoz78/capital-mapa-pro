/** @OnlyCurrentDoc */
// Uses installable edit events and one-shot continuation. No recurring timer.
const KFA_INCREMENTAL = Object.freeze({
  edit:'cerebroLabOnKnowledgeEdit', drain:'cerebroLabDrainIncremental',
  enabled:'KFA_INCREMENTAL_ENABLED', failures:'KFA_INCREMENTAL_ATTEMPTS',
  delay:60000, retry:300000, attempts:3
});

function cerebroIncrementalLocked_(action) {
  const lock=LockService.getDocumentLock();
  lock.waitLock(30000);
  try { return action(PropertiesService.getScriptProperties()); }
  finally { lock.releaseLock(); }
}
function cerebroIncrementalTriggers_(handler) {
  return ScriptApp.getProjectTriggers().filter(trigger=>trigger.getHandlerFunction()===handler);
}
function cerebroIncrementalClear_(handler) {
  cerebroIncrementalTriggers_(handler).forEach(trigger=>ScriptApp.deleteTrigger(trigger));
}
function cerebroIncrementalSchedule_(delay) {
  const old=cerebroIncrementalTriggers_(KFA_INCREMENTAL.drain);
  ScriptApp.newTrigger(KFA_INCREMENTAL.drain).timeBased().after(delay).create();
  old.forEach(trigger=>ScriptApp.deleteTrigger(trigger));
}
function cerebroLabInstallIncremental() {
  return cerebroIncrementalLocked_(properties=>{
    const cfg=cerebroConfig_();
    if (cfg.run_enabled!=='TRUE' || cfg.auto_trigger_enabled!=='FALSE' || cerebroIncrementalTriggers_('cerebroLabRunBatch').length) throw Error('LAB_INCREMENTAL_CONFIG_CONFLICT');
    const spreadsheet=SpreadsheetApp.getActiveSpreadsheet();
    const existing=cerebroIncrementalTriggers_(KFA_INCREMENTAL.edit);
    if (existing.length>1 || existing.some(t=>t.getTriggerSourceId()!==spreadsheet.getId())) throw Error('LAB_EDIT_TRIGGER_CONFLICT');
    const added=existing.length?null:ScriptApp.newTrigger(KFA_INCREMENTAL.edit).forSpreadsheet(spreadsheet).onEdit().create();
    try { properties.setProperty(KFA_INCREMENTAL.enabled,'TRUE'); }
    catch(error) { if (added) ScriptApp.deleteTrigger(added); throw error; }
    console.log('LAB_INCREMENTAL_ENABLED');
  });
}
function cerebroLabRemoveIncremental() {
  return cerebroIncrementalLocked_(properties=>{
    properties.deleteProperty(KFA_INCREMENTAL.enabled);
    cerebroIncrementalClear_(KFA_INCREMENTAL.edit);
    cerebroIncrementalClear_(KFA_INCREMENTAL.drain);
    properties.deleteProperty(KFA_INCREMENTAL.failures);
    console.log('LAB_INCREMENTAL_DISABLED');
  });
}
function cerebroLabOnKnowledgeEdit(event) {
  if (!event || !event.range) return;
  const name=event.range.getSheet().getName();
  if (![KFA.sheets.departments,KFA.sheets.agents,KFA.sheets.specialists,KFA.sheets.assignments,KFA.sheets.library].includes(name)) return;
  return cerebroLabQueueIncremental();
}
function cerebroLabQueueIncremental() {
  return cerebroIncrementalLocked_(properties=>{
    if (properties.getProperty(KFA_INCREMENTAL.enabled)!=='TRUE' || cerebroConfig_().run_enabled!=='TRUE') return;
    properties.deleteProperty(KFA_INCREMENTAL.failures);
    if (!cerebroIncrementalTriggers_(KFA_INCREMENTAL.drain).length) cerebroIncrementalSchedule_(KFA_INCREMENTAL.delay);
    console.log('LAB_INCREMENTAL_QUEUED');
  });
}
function cerebroLabDrainIncremental(event) {
  return cerebroIncrementalLocked_(properties=>{
    const timers=cerebroIncrementalTriggers_(KFA_INCREMENTAL.drain);
    if (event?.triggerUid && !timers.some(t=>t.getUniqueId()===event.triggerUid)) return;
    if (properties.getProperty(KFA_INCREMENTAL.enabled)!=='TRUE') {
      cerebroIncrementalClear_(KFA_INCREMENTAL.drain);
      return;
    }
    const count=Number(properties.getProperty(KFA_INCREMENTAL.failures)||'0');
    if (count>=KFA_INCREMENTAL.attempts) {
      cerebroIncrementalClear_(KFA_INCREMENTAL.drain);
      throw Error('LAB_INCREMENTAL_RETRY_LIMIT');
    }
    properties.setProperty(KFA_INCREMENTAL.failures,String(count+1));
    cerebroIncrementalSchedule_(KFA_INCREMENTAL.retry);
    const result=cerebroLabRunBatch();
    if (result.processed_total===result.total) {
      cerebroIncrementalClear_(KFA_INCREMENTAL.drain);
    } else if (result.processed_now) {
      cerebroIncrementalSchedule_(KFA_INCREMENTAL.delay);
    } else {
      const nextUtcDay=(Math.floor(Date.now()/86400000)+1)*86400000;
      cerebroIncrementalSchedule_(Math.max(KFA_INCREMENTAL.delay,nextUtcDay-Date.now()+KFA_INCREMENTAL.delay));
    }
    properties.deleteProperty(KFA_INCREMENTAL.failures);
    cerebroAppend_(KFA.sheets.audit,[[new Date().toISOString(),'APPS_SCRIPT','INCREMENTAL_DRAIN','LAB',result.processed_now,'PASS',JSON.stringify(result)]]);
    console.log(result.processed_total===result.total?'LAB_INCREMENTAL_IDLE':'LAB_INCREMENTAL_CONTINUATION');
    return result;
  });
}

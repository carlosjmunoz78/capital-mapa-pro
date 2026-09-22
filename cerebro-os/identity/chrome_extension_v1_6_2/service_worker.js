const PORTS = Array.from({length: 21}, (_, i) => 8765 + i);
const EXPECTED_SERVICE_VERSION = "1.4.1";
const EXTENSION_VERSION = "1.6.2";
const ALLOWED_URL = "https://example.com/";

async function getJson(url) {
  try {
    const response = await fetch(url, {method: "GET", cache: "no-store"});
    if (!response.ok) return null;
    return await response.json();
  } catch (_) {
    return null;
  }
}

async function waitForAllowedMetadata(tabId) {
  for (let i = 0; i < 20; i++) {
    try {
      const tab = await chrome.tabs.get(tabId);
      const url = String(tab.url || "");
      const title = String(tab.title || "");
      if (tab.status === "complete") {
        const good = url === ALLOWED_URL && title === "Example Domain";
        return {
          good, url: good ? ALLOWED_URL : "", title: good ? "Example Domain" : "",
          page_load_complete: good,
        };
      }
    } catch (_) {
      return {good:false, url:"", title:"", page_load_complete:false};
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  return {good:false, url:"", title:"", page_load_complete:false};
}

async function report(port, extensionId, cmd, success, metadata) {
  let url = "http://127.0.0.1:" + port + "/extension/result?extension_id=" +
    encodeURIComponent(extensionId) + "&command_id=" + encodeURIComponent(cmd.command_id) +
    "&result=" + (success ? "COMPLETED" : "FAILED");
  if (cmd.action === "READ_ONLY_PAGE_METADATA") {
    url += "&observed_url=" + encodeURIComponent(metadata.url || "") +
      "&observed_title=" + encodeURIComponent(metadata.title || "") +
      "&page_load_complete=" + (metadata.page_load_complete ? "true" : "false");
  }
  const receipt = await getJson(url);
  if (!receipt || receipt.status !== "GREEN") {
    console.warn("CEREBRO_LOCAL_RECEIPT_UNCONFIRMED", cmd.action, receipt?.decision || "NO_RESPONSE");
  }
  return Boolean(receipt && receipt.status === "GREEN");
}

const ACTIONS=new Set(["OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ"]);
function validCmd(c){return c&&c.environment==="LAB"&&c.company_id==="fenix"&&c.external_mutation_allowed===false&&ACTIONS.has(c.action)&&c.target_url&&c.target_url==="http://127.0.0.1:"+c.bridge_port+"/lab/operator-fixture"}
async function executeOperator(port,id,c){if(!validCmd({...c,bridge_port:port}))return;let result={good:false,evidence:"OPERATOR_FAILED",value:""};
 try{let tabs=await chrome.tabs.query({url:"http://127.0.0.1:"+port+"/*"});let tab=tabs.find(t=>t.url===c.target_url);if(!tab)tab=await chrome.tabs.create({url:c.target_url,active:false});if(!tab||!Number.isInteger(tab.id))throw new Error("FIXTURE_TAB_REQUIRED");for(let x=0;x<20;x++){const t=await chrome.tabs.get(tab.id);if(t.status==="complete")break;await new Promise(r=>setTimeout(r,300))}
 const out=await chrome.scripting.executeScript({target:{tabId:tab.id},func:(action,selector,value)=>{
   const allowed=new Set(["#cerebro-button","#cerebro-input","#cerebro-select","#cerebro-output"]);if(!allowed.has(selector))return {ok:false,reason:"SELECTOR_DENIED"};
   const el=document.querySelector(selector);if(!el)return {ok:false,reason:"ELEMENT_NOT_FOUND"};
   if(action==="OPERATOR_CLICK"){if(selector!=="#cerebro-button")return {ok:false,reason:"ACTION_SELECTOR_DENIED"};el.click();return {ok:true,value:document.querySelector("#cerebro-output")?.textContent||""}}
   if(action==="OPERATOR_TYPE"){if(selector!=="#cerebro-input"||typeof value!=="string"||value.length>64)return {ok:false,reason:"ACTION_SELECTOR_DENIED"};el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}));return {ok:true,value:el.value}}
   if(action==="OPERATOR_SELECT"){if(selector!=="#cerebro-select"||!["alpha","beta"].includes(value))return {ok:false,reason:"ACTION_SELECTOR_DENIED"};el.value=value;el.dispatchEvent(new Event("change",{bubbles:true}));return {ok:true,value:el.value}}
   if(action==="OPERATOR_READ"){if(selector!=="#cerebro-output")return {ok:false,reason:"ACTION_SELECTOR_DENIED"};return {ok:true,value:String(el.textContent||"").slice(0,64)}}
   return {ok:false,reason:"ACTION_DENIED"};
 },args:[c.action,c.selector||"",c.value||""]});
 const x=out?.[0]?.result;if(x?.ok)result={good:true,evidence:"LAB_OPERATOR_FIXTURE_VERIFIED",value:String(x.value||"").slice(0,64)};
 }catch{}
 let u="http://127.0.0.1:"+port+"/extension/operator-result?extension_id="+encodeURIComponent(id)+"&command_id="+encodeURIComponent(c.command_id)+"&result="+(result.good?"COMPLETED":"FAILED")+"&evidence="+encodeURIComponent(result.evidence)+"&observed_value="+encodeURIComponent(result.value);await getJson(u)}

async function execute(port, extensionId, cmd) {
  if (cmd.environment !== "LAB" || cmd.external_mutation_allowed !== false) return;
  if(ACTIONS.has(cmd.action)){await executeOperator(port,extensionId,cmd);return;}
  if (cmd.action === "OPEN_LOCAL_TEST_PAGE") {
    const url = "http://127.0.0.1:" + port + "/lab/test?command_id=" +
      encodeURIComponent(cmd.command_id);
    if (cmd.target_url !== url) return;
    // Fail closed: a command is recorded before any local tab opens.
    // Replayed/unacknowledged commands retry only their receipt, never the tab.
    // Multi-command fail-closed ledger. Do not overwrite A when B arrives.
    // Persistent CLAIMED entry precedes any side effect. An interrupted claim
    // never re-executes automatically: reconcile under human/policy control.
    const key = "cerebro_local_test_receipt_ledger_v162";
    const scope = [cmd.company_id, cmd.environment, cmd.command_id].join(":");
    const persisted = (await chrome.storage.local.get(key))[key];
    const ledger = persisted && typeof persisted === "object" && !Array.isArray(persisted) ? persisted : {};
    const previous = ledger[scope];
    if (previous) {
      // CLAIMED could mean the worker crashed between reserve and effect;
      // do not claim completion or run that effect twice.
      if (previous.phase === "TERMINAL") {
        await report(port, extensionId, cmd, previous.success === true, {});
      } else {
        console.warn("CEREBRO_LOCAL_COMMAND_AMBIGUOUS_NO_REPLAY", cmd.command_id);
      }
      return;
    }
    // Bounded storage without eviction of unfinished or terminal receipts.
    // When capacity is reached, fail closed and wait for explicit reconciliation.
    if (Object.keys(ledger).length >= 128) {
      console.warn("CEREBRO_LOCAL_RECEIPT_LEDGER_FULL");
      return;
    }
    ledger[scope] = {phase:"CLAIMED", success:false, created_at:Date.now()};
    await chrome.storage.local.set({[key]:ledger});
    let success = false;
    try {
      const tabs = await chrome.tabs.query({url:"http://127.0.0.1:" + port + "/*"});
      if (!tabs.some(tab => tab.url === url)) {
        const opened = await chrome.tabs.create({url, active:false});
        if (!opened || !Number.isInteger(opened.id)) throw new Error("TAB_NOT_CREATED");
      }
      success = true;
    } catch (error) {
      console.warn("CEREBRO_LOCAL_TEST_OPEN_FAILED", String(error?.message || "UNKNOWN").slice(0,80));
    }
    ledger[scope] = {phase:"TERMINAL", success, created_at:ledger[scope].created_at};
    await chrome.storage.local.set({[key]:ledger});
    await report(port, extensionId, cmd, success, {});
    return;
  }
  if (cmd.action !== "READ_ONLY_PAGE_METADATA" || cmd.target_url !== ALLOWED_URL) return;
  let metadata = {good:false, url:"", title:"", page_load_complete:false};
  try {
    const tab = await chrome.tabs.create({url: ALLOWED_URL, active:false});
    if (tab && Number.isInteger(tab.id)) {
      metadata = await waitForAllowedMetadata(tab.id);
    }
  } catch (_) {}
  await report(port, extensionId, cmd, metadata.good, metadata);
}

async function cyclePort(port) {
  const id = chrome.runtime.id;
  const ping = await getJson(
    "http://127.0.0.1:" + port + "/extension/ping?extension_id=" +
    encodeURIComponent(id) + "&extension_version=" + EXTENSION_VERSION
  );
  if (!ping || ping.status !== "GREEN" || ping.service_version !== EXPECTED_SERVICE_VERSION) return false;
  const cmd = await getJson(
    "http://127.0.0.1:" + port + "/extension/command?extension_id=" + encodeURIComponent(id)
  );
  if (!cmd || cmd.decision === "NO_COMMAND") return true;
  if (cmd.decision !== "LAB_COMMAND_AVAILABLE") return true;
  await execute(port, id, cmd);
  return true;
}

let heartbeatInFlight = null;
async function heartbeat() {
  if (heartbeatInFlight) return heartbeatInFlight;
  heartbeatInFlight = (async () => {
    for (const port of PORTS) {
      if (await cyclePort(port)) return true;
    }
    return false;
  })();
  try { return await heartbeatInFlight; }
  finally { heartbeatInFlight = null; }
}

chrome.runtime.onInstalled.addListener(async () => {
  await heartbeat();
  chrome.alarms.create("cerebro-heartbeat", {periodInMinutes: 1});
});
chrome.runtime.onStartup.addListener(async () => {
  await heartbeat();
  chrome.alarms.create("cerebro-heartbeat", {periodInMinutes: 1});
});
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === "cerebro-heartbeat") await heartbeat();
});
heartbeat();

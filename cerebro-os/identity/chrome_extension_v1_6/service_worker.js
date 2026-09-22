const PORTS = Array.from({length: 21}, (_, i) => 8765 + i);
const EXPECTED_SERVICE_VERSION = "1.4.1";
const EXTENSION_VERSION = "1.6.0";
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
  await getJson(url);
}

async function execute(port, extensionId, cmd) {
  if (cmd.environment !== "LAB" || cmd.external_mutation_allowed !== false) return;
  if (cmd.action === "OPEN_LOCAL_TEST_PAGE") {
    const url = "http://127.0.0.1:" + port + "/lab/test?command_id=" +
      encodeURIComponent(cmd.command_id);
    if (cmd.target_url !== url) return;
    let success = false;
    try {
      await chrome.tabs.create({url, active:false});
      success = true;
    } catch (_) {}
    await report(port, extensionId, cmd, success, {});
    return;
  }
  const OP_ACTIONS = ["OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ"];
  if (OP_ACTIONS.includes(cmd.action)) {
    // Only the internal localhost fixture. External writes are not executable.
    const fixture = "http://127.0.0.1:" + port + "/lab/operator-fixture";
    if (cmd.company_id !== "fenix" || cmd.target_url !== fixture ||
        !cmd.target_url.startsWith("http://127.0.0.1:") ||
        !["#cerebro-button","#cerebro-input","#cerebro-select","#cerebro-output"].includes(cmd.selector)) return;
    const expectedSelector = {
      OPERATOR_CLICK:"#cerebro-button", OPERATOR_TYPE:"#cerebro-input",
      OPERATOR_SELECT:"#cerebro-select", OPERATOR_READ:"#cerebro-output"
    }[cmd.action];
    if (cmd.selector !== expectedSelector ||
        (cmd.action === "OPERATOR_TYPE" && cmd.value !== "CEREBRO_LAB") ||
        (cmd.action === "OPERATOR_SELECT" && cmd.value !== "beta")) return;
    let result = {good:false,value:""};
    try {
      const tab = await chrome.tabs.create({url:fixture,active:false});
      if (!tab || !Number.isInteger(tab.id)) throw Error("TAB_CREATE_FAILED");
      let loaded = false;
      for (let i=0;i<20;i++) {
        const current = await chrome.tabs.get(tab.id);
        if (current.url !== fixture && current.status === "complete") break;
        if (current.url === fixture && current.status === "complete") {loaded=true;break;}
        await new Promise(resolve=>setTimeout(resolve,500));
      }
      if (!loaded) throw Error("FIXTURE_NOT_LOADED");
      const exec = await chrome.scripting.executeScript({
        target:{tabId:tab.id},
        func:(action,selector,value)=>{
          const allowed=new Set(["#cerebro-button","#cerebro-input","#cerebro-select","#cerebro-output"]);
          if(!allowed.has(selector) || location.origin !== "http://127.0.0.1:"+location.port ||
             location.pathname !== "/lab/operator-fixture") return {ok:false,value:""};
          const el=document.querySelector(selector);
          if(!el)return {ok:false,value:""};
          if(action==="OPERATOR_CLICK" && selector==="#cerebro-button"){
            el.click();return {ok:true,value:document.querySelector("#cerebro-output")?.textContent||""};
          }
          if(action==="OPERATOR_TYPE" && selector==="#cerebro-input" &&
             typeof value==="string" && value.length<=64){
            el.value=value;el.dispatchEvent(new Event("input",{bubbles:true}));return {ok:true,value:el.value};
          }
          if(action==="OPERATOR_SELECT" && selector==="#cerebro-select" &&
             ["alpha","beta"].includes(value)){
            el.value=value;el.dispatchEvent(new Event("change",{bubbles:true}));return {ok:true,value:el.value};
          }
          if(action==="OPERATOR_READ" && selector==="#cerebro-output")
            return {ok:true,value:String(el.textContent||"").slice(0,64)};
          return {ok:false,value:""};
        },args:[cmd.action,cmd.selector,cmd.value]
      });
      const out=exec?.[0]?.result;
      const expected={OPERATOR_CLICK:"CLICKED",OPERATOR_TYPE:"CEREBRO_LAB",
                      OPERATOR_SELECT:"beta",OPERATOR_READ:"READY"}[cmd.action];
      if(out?.ok && out.value===expected)result={good:true,value:expected};
    } catch(_){}
    const resultUrl = "http://127.0.0.1:" + port + "/extension/result?extension_id=" +
      encodeURIComponent(extensionId) + "&command_id=" + encodeURIComponent(cmd.command_id) +
      "&result=" + (result.good ? "COMPLETED":"FAILED") +
      "&observed_value=" + encodeURIComponent(result.value);
    await getJson(resultUrl);
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

async function heartbeat() {
  for (const port of PORTS) {
    if (await cyclePort(port)) return true;
  }
  return false;
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

const PORTS = Array.from({length: 21}, (_, i) => 8765 + i);
const EXPECTED_SERVICE_VERSION = "1.4.1";
const EXTENSION_VERSION = "1.5.0";
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

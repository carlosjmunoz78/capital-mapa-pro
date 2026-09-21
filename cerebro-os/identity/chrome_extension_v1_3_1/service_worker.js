const PORTS = Array.from({length: 21}, (_, i) => 8765 + i);
const EXPECTED_SERVICE_VERSION = "1.3.1";

async function requestJson(url) {
  try {
    const response = await fetch(url, {method: "GET", cache: "no-store"});
    if (!response.ok) return null;
    return await response.json();
  } catch (_) {
    return null;
  }
}

async function cyclePort(port) {
  const id = encodeURIComponent(chrome.runtime.id);
  const ping = await requestJson("http://127.0.0.1:" + port + "/extension/ping?extension_id=" + id);
  if (!ping || ping.status !== "GREEN" || ping.service_version !== EXPECTED_SERVICE_VERSION) return false;

  const cmd = await requestJson("http://127.0.0.1:" + port + "/extension/command?extension_id=" + id);
  if (!cmd || cmd.decision === "NO_COMMAND") return true;
  if (cmd.decision !== "LAB_COMMAND_AVAILABLE") return true;
  if (cmd.environment !== "LAB" || cmd.external_mutation_allowed !== false) return true;
  if (cmd.action !== "OPEN_LOCAL_TEST_PAGE") return true;
  if (!String(cmd.target_url || "").startsWith("http://127.0.0.1:" + port + "/lab/test?")) return true;

  let result = "FAILED";
  try {
    await chrome.tabs.create({url: cmd.target_url, active: false});
    result = "COMPLETED";
  } catch (_) {}

  const resultUrl = "http://127.0.0.1:" + port + "/extension/result?extension_id=" + id +
    "&command_id=" + encodeURIComponent(cmd.command_id) + "&result=" + result;
  await requestJson(resultUrl);
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

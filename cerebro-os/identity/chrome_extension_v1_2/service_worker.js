const PORTS = Array.from({length: 21}, (_, i) => 8765 + i);

async function pingPort(port) {
  const url = "http://127.0.0.1:" + port + "/extension/ping?extension_id=" + encodeURIComponent(chrome.runtime.id);
  try {
    const response = await fetch(url, {method: "GET", cache: "no-store"});
    if (!response.ok) return false;
    const payload = await response.json();
    return Boolean(
      payload &&
      payload.status === "GREEN" &&
      payload.decision === "EXTENSION_HEARTBEAT_ACCEPTED" &&
      payload.external_mutation_allowed === false &&
      payload.cloud_transport_configured === false
    );
  } catch (_) {
    return false;
  }
}

async function heartbeat() {
  for (const port of PORTS) {
    if (await pingPort(port)) return true;
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
  if (alarm.name === "cerebro-heartbeat") {
    await heartbeat();
  }
});

heartbeat();

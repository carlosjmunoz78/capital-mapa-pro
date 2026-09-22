const PORTS=Array.from({length:21},(_,i)=>8765+i);
const EXPECTED_SERVICE_VERSION="1.4.1",EXTENSION_VERSION="1.6.0";
const ACTIONS=new Set(["OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ"]);
async function getJson(url){try{const r=await fetch(url,{method:"GET",cache:"no-store"});return r.ok?await r.json():null}catch{return null}}
function validCmd(c){return c&&c.environment==="LAB"&&c.company_id==="fenix"&&c.external_mutation_allowed===false&&ACTIONS.has(c.action)&&c.target_url&&c.target_url.startsWith("http://127.0.0.1:")}
async function execute(port,id,c){if(!validCmd(c))return;let result={good:false,evidence:"OPERATOR_FAILED",value:""};
 try{const tabs=await chrome.tabs.query({url:"http://127.0.0.1:"+port+"/*"});const tab=tabs.find(t=>t.url===c.target_url);if(!tab||!Number.isInteger(tab.id))throw new Error("FIXTURE_TAB_REQUIRED");
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
async function cycle(port){const id=chrome.runtime.id,p=await getJson("http://127.0.0.1:"+port+"/extension/ping?extension_id="+encodeURIComponent(id)+"&extension_version="+EXTENSION_VERSION);if(!p||p.status!=="GREEN"||p.service_version!==EXPECTED_SERVICE_VERSION)return false;const c=await getJson("http://127.0.0.1:"+port+"/extension/command?extension_id="+encodeURIComponent(id));if(c?.decision==="LAB_COMMAND_AVAILABLE")await execute(port,id,c);return true}
async function heartbeat(){for(const p of PORTS)if(await cycle(p))return true;return false}
chrome.runtime.onInstalled.addListener(async()=>{await heartbeat();chrome.alarms.create("cerebro-heartbeat",{periodInMinutes:1})});chrome.runtime.onStartup.addListener(async()=>{await heartbeat();chrome.alarms.create("cerebro-heartbeat",{periodInMinutes:1})});chrome.alarms.onAlarm.addListener(async a=>{if(a.name==="cerebro-heartbeat")await heartbeat()});heartbeat();

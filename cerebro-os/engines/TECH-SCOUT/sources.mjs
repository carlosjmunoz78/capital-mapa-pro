// TECH-SCOUT · 14 public sources · strictly bounded metadata-only LAB probes.
export const SOURCES = Object.freeze({
  BOE: {url:"https://www.boe.es/datosabiertos/api/boe/sumario/20261120",kind:"json",mode:"READ_ONLY"},
  INE: {url:"https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/68026?nult=1",kind:"json",mode:"READ_ONLY"},
  EUROSTAT: {url:"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjan?geo=ES&age=TOTAL&sex=T&time=2024",kind:"json",mode:"READ_ONLY"},
  ECB: {url:"https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A?startPeriod=2026-11-18&endPeriod=2026-11-20",kind:"xml",mode:"READ_ONLY"},
  WORLD_BANK: {url:"https://api.worldbank.org/v2/country/ESP/indicator/SP.POP.TOTL?format=json&per_page=1",kind:"json",mode:"READ_ONLY"},
  CROSSREF: {url:"https://api.crossref.org/works?rows=1&query.title=real%20estate",kind:"json",mode:"READ_ONLY"},
  COMMONS: {url:"https://commons.wikimedia.org/w/api.php?action=query&meta=siteinfo&siprop=general&format=json",kind:"json",mode:"READ_ONLY"},
  WIKIDATA: {url:"https://query.wikidata.org/sparql?query=ASK%20%7B%20wd%3AQ29%20wdt%3AP31%20wd%3AQ6256%20%7D&format=json",kind:"json",mode:"READ_ONLY"},
  OPENVERSE: {url:"https://api.openverse.org/v1/images/?q=cordoba&page_size=1",kind:"json",mode:"LICENSE_PER_ITEM"},
  CATASTRO: {url:"https://ovc.catastro.meh.es/ovcservweb/ovcswlocalizacionrc/ovccallejero.asmx?WSDL",kind:"xml",mode:"DISCOVERY_ONLY_NO_MASS_EXTRACTION"},
  PNOA: {url:"https://www.ign.es/wms-inspire/pnoa-ma?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0",kind:"xml",mode:"DISCOVERY_ONLY_ATTRIBUTION"},
  QUICKCHART: {url:"https://quickchart.io/chart?w=90&h=90&c=%7Btype%3A%27bar%27%2Cdata%3A%7Blabels%3A%5B%27X%27%5D%2Cdatasets%3A%5B%7Bdata%3A%5B1%5D%7D%5D%7D%7D",kind:"png",mode:"NO_PRIVATE_DATA"},
  GDELT: {url:"https://data.gdeltproject.org/gdeltv2/lastupdate.txt",kind:"text",mode:"FEED_ONLY_DOC_UNRELIABLE"},
  OVERPASS: {url:null,kind:"json",mode:"DISABLED_UNRELIABLE_FROM_VERCEL"}
});
const id = /^[a-zA-Z0-9_-]{12,64}$/;
export function validateRequest(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) return "INVALID_REQUEST";
  const expected = ["company_id","engine_id","environment","version","capability","provider","request_id"];
  if (Object.keys(input).length !== expected.length || Object.keys(input).some(k => !expected.includes(k))) return "UNEXPECTED_FIELD";
  if (input.company_id !== "fenix-capital" || input.engine_id !== "TECH-SCOUT") return "TENANT_DENIED";
  if (input.environment !== "LAB" || input.version !== "0.1.0" || input.capability !== "TECHSCOUT.PROBE") return "SCOPE_DENIED";
  if (typeof input.request_id !== "string" || !id.test(input.request_id)) return "INVALID_REQUEST_ID";
  if (typeof input.provider !== "string" || !Object.hasOwn(SOURCES,input.provider)) return "PROVIDER_DENIED";
  if (SOURCES[input.provider].url === null) return "PROVIDER_DEGRADED";
  return null;
}
export async function readLimited(response, maxBytes=65536) {
  if(!response.body || !response.body.getReader) return {text:"",bytes:0,overLimit:true};
  const reader=response.body.getReader(); let total=0; const chunks=[];
  try {
    while (true) {
      const {done,value}=await reader.read();
      if(done) break;
      total+=value.byteLength;
      if(total>maxBytes) return {text:"",bytes:total,overLimit:true};
      chunks.push(value);
    }
  } finally { try{await reader.cancel()}catch{} }
  const output = new Uint8Array(total); let i=0;
  for(const chunk of chunks){output.set(chunk,i);i+=chunk.byteLength}
  return {text:new TextDecoder().decode(output),bytes:total,overLimit:false};
}
export function shapeMatches(kind,contentType,text) {
  if(kind==="png") return contentType.includes("image/png");
  if(kind==="xml") return /xml/.test(contentType)&&/(\<\?xml|\<\w+[:\w]*\b)/i.test(text);
  if(kind==="text") return contentType.includes("text/plain")&&text.includes("http");
  if(kind==="json"){
    if(!/(json|sparql-results)/.test(contentType)) return false;
    try {const x=JSON.parse(text);return x!==null&&typeof x==="object"}catch{return false}
  }
  return false;
}
export async function sameSecret(input,expected) {
  if(typeof input!=="string" || typeof expected!=="string" || expected.length<48 || input.length>512) return false;
  const encoder=new TextEncoder();
  const [a,b]=await Promise.all([crypto.subtle.digest("SHA-256",encoder.encode(input)),crypto.subtle.digest("SHA-256",encoder.encode(expected))]);
  let diff=0;const left=new Uint8Array(a),right=new Uint8Array(b);
  for(let i=0;i<left.length;i++)diff|=left[i]^right[i];
  return diff===0;
}
export async function probe(input,callerToken,env,fetcher=fetch,now=Date.now()) {
  const error=validateRequest(input);
  if(error) return {status:"DENIED",reason:error};
  if(env.TECHSCOUT_ENABLED!=="true" || env.TECHSCOUT_PUBLIC_PROBE_ENABLED!=="true") return {status:"DISABLED",reason:"LAB_OFF"};
  if(!await sameSecret(callerToken,env.TECHSCOUT_CALLER_TOKEN))return{status:"DENIED",reason:"AUTH_DENIED"};
  if(!env.LAB_KV || typeof env.LAB_KV.put!=="function" || typeof env.LAB_KV.get!=="function")return {status:"DENIED",reason:"AUDIT_NOT_READY"};
  const key="techscout/v0.1.0/probe/"+input.request_id;
  const prior=await env.LAB_KV.get(key);
  if(prior!==null) return {status:"DENIED",reason:"DUPLICATE"};
  const logBase={company_id:input.company_id,engine_id:input.engine_id,environment:"LAB",provider:input.provider,request_id:input.request_id};
  try {await env.LAB_KV.put(key,JSON.stringify({...logBase,status:"STARTED",ts:now}),{expirationTtl:86400*30})}
  catch {return {status:"DENIED",reason:"AUDIT_WRITE_FAILED"}}
  const source=SOURCES[input.provider];let result;
  try {
    const r=await fetcher(source.url,{method:"GET",redirect:"manual",headers:{"accept":"application/json, application/xml, text/xml, text/plain, image/png;q=0.8","user-agent":"CEREBRO-TECHSCOUT-LAB/0.1"},signal:AbortSignal.timeout(7000)});
    const contentType=(r.headers.get("content-type")||"").slice(0,100);
    const sample=await readLimited(r);
    const valid=r.ok&&!sample.overLimit&&shapeMatches(source.kind,contentType,sample.text);
    result={status:valid?"PASS":"DEGRADED",provider:input.provider,http:r.status,shape_ok:valid,kind:source.kind,bytes:sample.bytes,mode:source.mode};
  } catch (e) {result={status:"DEGRADED",provider:input.provider,reason:e.name==="TimeoutError"?"TIMEOUT":"UPSTREAM_FAILURE"}}
  try {await env.LAB_KV.put(key,JSON.stringify({...logBase,status:result.status,http:result.http||null,ts:now}),{expirationTtl:86400*30})}
  catch {return {status:"DENIED",reason:"AUDIT_FINAL_FAILED"}}
  return result;
}

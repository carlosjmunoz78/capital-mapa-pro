const ISSUER="https://token.actions.githubusercontent.com";
const REPOSITORY="carlosjmunoz78/capital-mapa-pro";
const REF="refs/heads/cerebro/knowledge-factory-appsscript-lab-v0-20261119";
const WORKFLOW=REPOSITORY+"/.github/workflows/cerebro-ums001-knowledge-oidc-lab.yml@";
const MERGE_REF="refs/pull/278/merge";
function allowedTrigger(c){
  return (c.event_name==="push"&&c.ref===REF&&c.workflow_ref===WORKFLOW+REF&&
    c.sub==="repo:"+REPOSITORY+":ref:"+REF)||
    (c.event_name==="pull_request"&&c.ref===MERGE_REF&&c.workflow_ref===WORKFLOW+MERGE_REF&&
     c.head_ref==="cerebro/knowledge-factory-appsscript-lab-v0-20261119"&&c.base_ref==="cerebro-engine-factory-v0"&&
     c.sub==="repo:"+REPOSITORY+":pull_request");
}
export const AUDIENCE="https://cerebro-knowledge-agent-bridge-lab.carlosj-munozcabeza.workers.dev/ums";
const encoder=new TextEncoder();
// Published GitHub signing keys, independently retrieved over HTTPS for this
// time-limited rehearsal. Fail closed after the protected preview grant ends.
const FALLBACK_KEYS=[{"kty":"RSA","alg":"RS256","use":"sig","kid":"cc413527-173f-5a05-976e-9c52b1d7b431","n":"w4M936N3ZxNaEblcUoBm-xu0-V9JxNx5S7TmF0M3SBK-2bmDyAeDdeIOTcIVZHG-ZX9N9W0u1yWafgWewHrsz66BkxXq3bscvQUTAw7W3s6TEeYY7o9shPkFfOiU3x_KYgOo06SpiFdymwJflRs9cnbaU88i5fZJmUepUHVllP2tpPWTi-7UA3AdP3cdcCs5bnFfTRKzH2W0xqKsY_jIG95aQJRBDpbiesefjuyxcQnOv88j9tCKWzHpJzRKYjAUM6OPgN4HYnaSWrPJj1v41eEkFM1kORuj-GSH2qMVD02VklcqaerhQHIqM-RjeHsN7G05YtwYzomE5G-fZuwgvQ","e":"AQAB"},{"kty":"RSA","alg":"RS256","use":"sig","kid":"38826b17-6a30-5f9b-b169-8beb8202f723","n":"5Manmy-zwsk3wEftXNdKFZec4rSWENW4jTGevlvAcU9z3bgLBogQVvqYLtu9baVm2B3rfe5onadobq8po5UakJ0YsTiiEfXWdST7YI2Sdkvv-hOYMcZKYZ4dFvuSO1vQ2DgEkw_OZNiYI1S518MWEcNxnPU5u67zkawAGsLlmXNbOylgVfBRJrG8gj6scr-sBs4LaCa3kg5IuaCHe1pB-nSYHovGV_z0egE83C098FfwO1dNZBWeo4Obhb5Z-ZYFLJcZfngMY0zJnCVNmpHQWOgxfGikh3cwi4MYrFrbB4NTlxbrQ3bL-rGKR5X318veyDlo8Dyz2KWMobT4wB9U1Q","e":"AQAB"},{"kty":"RSA","alg":"RS256","use":"sig","kid":"38E9B30B3A023A1B72309921A69A42FCC496C42C","n":"tEq2Fp9HcdT5MwMsB_UTm8j_woJJLi3sA-y0RX2tioTm581seyfvOH6lJ5JmHVtS-_fb8B2tRT1pznHQSNq14PsJdu9bp5egbWmIz-5RvhqoM-oKem_MJENCNFuqXijRLT47FRdfH3inqde1vJlA_JJHCqYMKIpHH7kqNFYcCpwr0vk80Hc2rTyL0uBXI7NqBZbtUgNoyucWO5O7QQrPNOmlr-GI8aFckFRfobCaCOiH9qW02FtkV74fwBGVCNhNf3a1CK81-O8xEGimvVydI_pQA5B8QqVuQjY_ntOu555HdirA0hKkY6fsE9eZCMFmWDHZ2kSWLjhabxWxIzSzXQ","e":"AQAB"},{"kty":"RSA","alg":"RS256","use":"sig","kid":"4F3E9AD8C9A6F5EB3173006F4FA630E28F43DCE9","n":"tGevqhkBGn8NB0dKxs8Ddxhn-xZPm55svcSlkJZEOwDOXDLl_0-iVOVKNJfcHHLHvMqa6zh2DDcpAWZi2FpeBAJupsrymqwzllxOODWKWoVIoaIjOO7h1JLiF9Knwuq-o6BPtKdwOT-bOrXRzChMtQsc5C1Auex-D0Z6loObBuK1Lkm0RK9ISQsLqBEwq8g0OOupI_shU1r2rT2G0nkZ0CvxVlQeUGShFi8Mdys2s5LPqBwjC4LKwjk8moWQV32KEccbTPKxnG_539DxRglHJgHPHisSVGsfZIUXi2chtXdQHZPdVve8ZRmknCykZtkJ6K87llSUXi7oyzhCIZdiUQ","e":"AQAB"}];
const FALLBACK_END=1795367708;

function decode(value){
  if(!/^[A-Za-z0-9_-]+$/.test(value)) throw Error("OIDC_DENIED");
  const raw=value.replace(/-/g,"+").replace(/_/g,"/");
  return Uint8Array.from(atob(raw.padEnd(Math.ceil(raw.length/4)*4,"=")),c=>c.charCodeAt(0));
}

export async function verifyUmsOidc(header,fetchKeys=(...args)=>fetch(...args),now=Math.floor(Date.now()/1000)){
  if(typeof header!=="string"||!header.startsWith("Bearer ")||header.length>10000) throw Error("OIDC_DENIED");
  const parts=header.slice(7).split(".");
  if(parts.length!==3) throw Error("OIDC_DENIED");
  const decoder=new TextDecoder();
  let protectedHeader,claims;
  try {[protectedHeader,claims]=parts.slice(0,2).map(value=>JSON.parse(decoder.decode(decode(value))));}
  catch {throw Error("OIDC_DECODE")}
  if(protectedHeader.alg!=="RS256"||typeof protectedHeader.kid!=="string"||protectedHeader.kid.length>128)throw Error("OIDC_HEADER");
  if(claims.iss!==ISSUER||claims.aud!==AUDIENCE||claims.repository!==REPOSITORY||
     String(claims.repository_id)!=="1139292249"||!allowedTrigger(claims))throw Error("OIDC_CONTEXT");
  if(!Number.isSafeInteger(claims.nbf)||claims.nbf>now+10||!Number.isSafeInteger(claims.iat)||
     claims.iat>now+10||claims.iat<now-360||!Number.isSafeInteger(claims.exp)||claims.exp<=now||
     claims.exp-claims.iat>600)throw Error("OIDC_TIME");
  if(!/^\d{1,20}$/.test(claims.run_id)||!/^\d{1,8}$/.test(claims.run_attempt)||
     !/^[a-f0-9]{40}$/.test(claims.sha))throw Error("OIDC_RUN");
  let keys;
  try {
    const response=await fetchKeys(ISSUER+"/.well-known/jwks",{redirect:"error",headers:{accept:"application/json"}});
    if(!response.ok)throw Error("KEYS_HTTP");
    keys=(await response.json()).keys;
    if(!Array.isArray(keys))throw Error("KEYS_PARSE");
  }catch {
    if(now>=FALLBACK_END)throw Error("OIDC_KEYS_UNAVAILABLE");
    keys=FALLBACK_KEYS;
  }
  const jwk=keys?.find(k=>k.kid===protectedHeader.kid&&k.kty==="RSA"&&
    (!k.alg||k.alg==="RS256")&&(!k.use||k.use==="sig"));
  if(!jwk) throw Error("OIDC_KID");
  let key,verified;
  try {key=await crypto.subtle.importKey("jwk",jwk,{name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"},false,["verify"]);}
  catch {throw Error("OIDC_KEY_IMPORT")}
  try {verified=await crypto.subtle.verify("RSASSA-PKCS1-v1_5",key,decode(parts[2]),encoder.encode(parts[0]+"."+parts[1]));}
  catch {throw Error("OIDC_VERIFY_RUNTIME")}
  if(!verified)throw Error("OIDC_SIGNATURE");
  return {request_id:"ums-"+claims.run_id+"-"+claims.run_attempt,commit:claims.sha};
}
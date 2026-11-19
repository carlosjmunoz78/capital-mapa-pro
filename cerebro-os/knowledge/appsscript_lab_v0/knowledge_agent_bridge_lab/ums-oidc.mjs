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

function decode(value){
  if(!/^[A-Za-z0-9_-]+$/.test(value)) throw Error("OIDC_DENIED");
  return Uint8Array.from(atob(value.replace(/-/g,"+").replace(/_/g,"/")), c=>c.charCodeAt(0));
}

export async function verifyUmsOidc(header,fetchKeys=fetch,now=Math.floor(Date.now()/1000)){
  if(typeof header!=="string"||!header.startsWith("Bearer ")||header.length>10000) throw Error("OIDC_DENIED");
  const parts=header.slice(7).split(".");
  if(parts.length!==3) throw Error("OIDC_DENIED");
  const decoder=new TextDecoder();
  const [protectedHeader,claims]=parts.slice(0,2).map(value=>JSON.parse(decoder.decode(decode(value))));
  if(protectedHeader.alg!=="RS256"||!/^[A-Za-z0-9_-]{1,128}$/.test(protectedHeader.kid)||claims.iss!==ISSUER||
     claims.aud!==AUDIENCE||claims.repository!==REPOSITORY||String(claims.repository_id)!=="1139292249"||
     !allowedTrigger(claims)||
     !Number.isSafeInteger(claims.nbf)||claims.nbf>now+10||!Number.isSafeInteger(claims.iat)||
     claims.iat>now+10||claims.iat<now-360||!Number.isSafeInteger(claims.exp)||claims.exp<=now||
     claims.exp-claims.iat>600||!/^\d{1,20}$/.test(claims.run_id)||!/^\d{1,8}$/.test(claims.run_attempt)||
     !/^[a-f0-9]{40}$/.test(claims.sha)) throw Error("OIDC_DENIED");
  const keys=await fetchKeys(ISSUER+"/.well-known/jwks",{redirect:"error"});
  if(!keys.ok) throw Error("OIDC_KEYS_UNAVAILABLE");
  const jwk=(await keys.json()).keys?.find(k=>k.kid===protectedHeader.kid&&k.kty==="RSA"&&
    (!k.alg||k.alg==="RS256")&&(!k.use||k.use==="sig"));
  if(!jwk) throw Error("OIDC_DENIED");
  const key=await crypto.subtle.importKey("jwk",jwk,{name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"},false,["verify"]);
  if(!await crypto.subtle.verify("RSASSA-PKCS1-v1_5",key,decode(parts[2]),encoder.encode(parts[0]+"."+parts[1]))) throw Error("OIDC_DENIED");
  return {request_id:"ums-"+claims.run_id+"-"+claims.run_attempt,commit:claims.sha};
}
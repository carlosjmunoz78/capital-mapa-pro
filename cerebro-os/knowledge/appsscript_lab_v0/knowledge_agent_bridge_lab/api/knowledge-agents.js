'use strict';
const {createPublicKey,verify}=require('node:crypto');
const {createLabGatewayKnowledgeCapability, SERVICE_ACCOUNT, CONNECTOR_ID}=require('../lab/gateway_runtime_lab_binding.cjs');
const GRANT=Object.freeze({"company_id":"fenix-capital","department_id":"facebook","engine_id":"SOC-FB-FINANCIAL-REAL-ESTATE-V1","agent_id":"FB-00","subagent_id":"FB-00.SA-001","environment":"LAB","version":"2026-11-18.v1"});
const UMS=Object.freeze({"company_id":"fenix","department_id":"ums","engine_id":"FACT-OIDC-LAB-E2E-001","agent_id":"FACT-OIDC-LAB-E2E-001","subagent_id":"FACT-OIDC-LAB-E2E-001","environment":"LAB","version":"0.1.0"});
const keys=new Map([
  ["fb-shadow-private-lab-v1",{grant:GRANT,spki:"MCowBQYDK2VwAyEANb24gN7uMiAJFJ1e8PwXqCAOMFfnpZ605LDLsMRi1HA="}],
  ["ums-github-oidc-lab-v1",{grant:UMS,spki:"MCowBQYDK2VwAyEASs7OCUlgnspqE4NMpw5SuohONWFfwF045qJvTb2Ugsc="}],
]);
const project='prj_LxPzJA5AkHJvhYzTAbVJbRrAvvLu';
const owner='team_qnh6u1Ofy2WPp0MGEKlyMA50';
const team='carlosjmunozcabeza-2582s-projects';
const projectName='cerebro-fact001-vercel-lab-20261111';
const provider='//iam.googleapis.com/projects/15609183753/locations/global/workloadIdentityPools/knowledge-vercel-lab/providers/preview';
const sheetScope='https://www.googleapis.com/auth/spreadsheets.readonly';
const audience='https://vercel.com/'+team;
const subject='owner:'+team+':project:'+projectName+':environment:preview';

async function token(req){
  const jwt=req.headers['x-vercel-oidc-token'] || process.env.VERCEL_OIDC_TOKEN;
  if(typeof jwt!=='string'||jwt.length>16000||jwt.split('.').length!==3) throw Error('WIF_UNAVAILABLE');
  const claims=JSON.parse(Buffer.from(jwt.split('.')[1],'base64url').toString('utf8'));
  if(claims.project_id!==project||claims.owner_id!==owner||claims.environment!=='preview'||
     claims.sub!==subject||claims.aud!==audience||
     !['https://oidc.vercel.com','https://oidc.vercel.com/'+team].includes(claims.iss)) throw Error('WIF_SCOPE_DENIED');
  const sts=await fetch('https://sts.googleapis.com/v1/token',{
    method:'POST',redirect:'error',signal:AbortSignal.timeout(10000),
    headers:{'content-type':'application/x-www-form-urlencoded'},
    body:new URLSearchParams({audience:provider,grant_type:'urn:ietf:params:oauth:grant-type:token-exchange',
      requested_token_type:'urn:ietf:params:oauth:token-type:access_token',scope:'https://www.googleapis.com/auth/cloud-platform',
      subject_token_type:'urn:ietf:params:oauth:token-type:jwt',subject_token:jwt})
  });
  if(!sts.ok) throw Error('STS_DENIED');
  const {access_token}=await sts.json();
  if(!access_token) throw Error('STS_TOKEN_MISSING');
  const google=await fetch('https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/'+SERVICE_ACCOUNT+':generateAccessToken',
    {method:'POST',redirect:'error',signal:AbortSignal.timeout(10000),
     headers:{authorization:'Bearer '+access_token,'content-type':'application/json'},
     body:JSON.stringify({scope:[sheetScope],lifetime:'600s'})});
  if(!google.ok) throw Error('IAM_DENIED');
  return (await google.json()).accessToken;
}

function verifyMachine(body,hostname){
  if(typeof body==='string'){if(body.length>8000)return null;try{body=JSON.parse(body)}catch{return null}}
  if(typeof body?.payload!=='string'||body.payload.length>7000||!/^[A-Za-z0-9_-]+$/.test(body.payload)||
     typeof body.signature!=='string'||!/^[A-Za-z0-9_-]{86}$/.test(body.signature)) return null;
  const signed=JSON.parse(Buffer.from(body.payload,'base64url').toString('utf8'));
  const principal=keys.get(signed.issuer);
  if(!principal)return null;
  const key=createPublicKey({key:Buffer.from(principal.spki,'base64'),format:'der',type:'spki'});
  if(!verify(null,Buffer.from(body.payload),key,Buffer.from(body.signature,'base64url')))return null;
  const now=Math.floor(Date.now()/1000);
  if(signed.subject!==principal.grant.subagent_id||signed.audience!==hostname||
     !Number.isSafeInteger(signed.iat)||signed.iat>now+5||signed.iat<now-90||
     !/^(fb|ums)-[a-z0-9-]{4,60}$/.test(signed.request_id)||
     !['prepare','read'].includes(signed.phase)) return null;
  return {signed,grant:principal.grant};
}

module.exports=async(req,res)=>{
  res.setHeader('Cache-Control','no-store');
  res.setHeader('X-Content-Type-Options','nosniff');
  if(process.env.VERCEL_ENV!=='preview')return res.status(404).end();
  if(req.method==='GET')return res.status(200).json({status:'MACHINE_AUTH_REQUIRED'});
  if(req.method!=='POST')return res.status(405).json({status:'METHOD_DENIED'});
  let machine;
  try{machine=verifyMachine(req.body,process.env.VERCEL_URL)}
  catch{return res.status(401).json({status:'IDENTITY_DENIED'})}
  if(!machine)return res.status(401).json({status:'IDENTITY_DENIED'});
  const {signed,grant}=machine;
  if(!Object.keys(grant).every(field=>signed.scope?.[field]===grant[field])){
    return res.status(403).json({status:'SCOPE_DENIED'});
  }
  if(process.env.CEREBRO_KNOWLEDGE_LAB_DISABLED==='true')return res.status(503).json({status:'CAPABILITY_DISABLED'});
  const principal={verified:true,id:grant.subagent_id,environment:'LAB',service_account_email:SERVICE_ACCOUNT};
  const binding=createLabGatewayKnowledgeCapability({
    enabled:true,authenticateRuntime:ctx=>ctx===signed?principal:null,readTrustedGrants:()=>[grant],
    routeGateway:input=>({...input,status:'ROUTED',connector_id:CONNECTOR_ID}),
    policyCheck:()=>true,googleAccessToken:()=>token(req),
    persistAudit:event=>{
      // The bound Worker records the authorization first, then signs the read
      // request with that exact digest. This path returns no data at prepare.
      if(signed.phase==='read'&&event.outcome==='READ_VERIFIED'&&event.sha256!==signed.sha256)throw Error('INTEGRITY_DENIED');
    }
  });
  try{
    const result=await binding.read(signed,signed.scope);
    return res.status(200).json(signed.phase==='prepare'?{sha256:result.sha256}:result);
  }catch(error){
    const reason=error?.message;
    if(reason==='INTEGRITY_DENIED')return res.status(409).json({status:reason});
    if(reason==='DELIVERY_RECEIPT_PENDING')return res.status(409).json({status:reason});
    return res.status(503).json({status:/^[A-Z0-9_]{1,45}$/.test(reason)?reason:'KNOWLEDGE_UNAVAILABLE'});
  }
};
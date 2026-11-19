'use strict';
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {createLabKnowledgeReader} = require('./gateway_sheets_lab.cjs');

const serviceAccount = 'cerebro-knowledge-reader-lab@cerebro-forge.iam.gserviceaccount.com';
const fields = ['company_id', 'department_id', 'engine_id', 'agent_id', 'subagent_id', 'environment', 'version'];
const grants = [
  {
    "company_id": "fenix-capital",
    "department_id": "facebook",
    "engine_id": "SOC-FB-FINANCIAL-REAL-ESTATE-V1",
    "agent_id": "FB-00",
    "subagent_id": "FB-00.SA-001",
    "environment": "LAB",
    "version": "2026-11-18.v1"
  },
  {
    "company_id": "fenix-capital",
    "department_id": "instagram",
    "engine_id": "SOC-001/SOCBOOT-001",
    "agent_id": "IG-00",
    "subagent_id": "IG-00.SA-001",
    "environment": "LAB",
    "version": "1.0.0-candidate"
  },
  {
    "company_id": "fenix-capital",
    "department_id": "linkedin",
    "engine_id": "SOC-LI-FINANCIAL-REAL-ESTATE-V1",
    "agent_id": "LI-00",
    "subagent_id": "LI-00.SA-001",
    "environment": "LAB",
    "version": "0.1.0"
  },
  {
    "company_id": "fenix",
    "department_id": "seo",
    "engine_id": "SEO-001",
    "agent_id": "SEO-D01:DEPARTMENT_HEAD",
    "subagent_id": "SEO-D01:SPECIALIST:01",
    "environment": "LAB",
    "version": "1.0.0"
  }
];
const caller = Symbol('verified-cloud-shell-probe');
const expectedOperator = process.argv[2];
if (!expectedOperator || !expectedOperator.includes('@')) throw new Error('OPERATOR_REQUIRED');
const gcloud = (...args) => {
  try { return execFileSync('gcloud', args, {encoding:'utf8', stdio:['ignore','pipe','ignore'],timeout:20000}).trim(); }
  catch { throw new Error('GOOGLE_CLOUD_SHELL_SESSION_UNAVAILABLE'); }
};
const authenticate = context => {
  if (context !== caller || gcloud('auth','list','--filter=status:ACTIVE','--format=value(account)') !== expectedOperator) return null;
  return {id: serviceAccount, grants};
};
const policyCheck = (principal, scope) => principal.id === serviceAccount && scope.environment === 'LAB' &&
  grants.some(grant=>fields.every(key=>grant[key]===scope[key]));
let tokenPromise;
function googleAccessToken() {
  tokenPromise ??= (async () => {
    const operatorToken = gcloud('auth','print-access-token','--quiet');
    const response = await fetch('https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/' + serviceAccount + ':generateAccessToken', {
      method:'POST', redirect:'error', signal:AbortSignal.timeout(15000),
      headers:{Authorization:'Bearer '+operatorToken,'Content-Type':'application/json'},
      body:JSON.stringify({scope:['https://www.googleapis.com/auth/spreadsheets.readonly'], lifetime:'600s'}),
    });
    if (!response.ok) throw new Error('GOOGLE_IMPERSONATION_HTTP_' + response.status);
    return (await response.json()).accessToken;
  })();
  return tokenPromise;
}
const reader = createLabKnowledgeReader({authenticate, policyCheck, googleAccessToken, audit: event => console.log(JSON.stringify(event))});

async function main() {
  await assert.rejects(reader(caller,{...grants[0], company_id:'other-company'}),/SCOPE_DENIED/);
  await assert.rejects(reader(caller,{...grants[0], version:'other-version'}),/SCOPE_DENIED/);
  let count=0;
  for (const request of grants) {
    try { await reader(caller,request); count++; }
    catch (error) {
      if (error.message !== 'DELIVERY_RECEIPT_PENDING') throw error;
      console.log(JSON.stringify({status:'PENDING_RECEIPT', department:request.department_id}));
    }
  }
  console.log(JSON.stringify({verified_reads:count, required:3, foreign_company_rejected:true, wrong_version_rejected:true}));
  if (count < 3) process.exitCode=2;
}
main().catch(error => {
  console.error(/^[A-Z0-9_]+$/.test(error.message) ? error.message : 'GATEWAY_PROBE_ERROR');
  process.exitCode=1;
});

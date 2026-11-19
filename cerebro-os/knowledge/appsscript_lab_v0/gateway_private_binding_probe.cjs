'use strict';
const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const {appendFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {createLabGatewayKnowledgeCapability, REQUIRED_SCOPE, SERVICE_ACCOUNT} = require('./gateway_runtime_lab_binding.cjs');

const serviceAccount = SERVICE_ACCOUNT;
const auditPath = process.argv[3];
if (!auditPath) throw new Error('AUDIT_PATH_REQUIRED');
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
// Private one-shot probe. This boundary verifies the existing gcloud operator
// session and uses its existing expiring IAM delegation. It is not a deployed consumer.
const authenticateRuntime = context => {
  if (context !== caller || gcloud('auth','list','--filter=status:ACTIVE','--format=value(account)') !== expectedOperator) return null;
  return {id: 'cloud-shell-operator-probe', verified: true, environment:'LAB', service_account_email:serviceAccount};
};
const policyCheck = (principal, scope) => principal.id === 'cloud-shell-operator-probe' &&
  grants.some(grant=>fields.every(key=>grant[key]===scope[key]));
const PYTHON_ROUTE = "import json, sys\nsys.path[:0] = sys.argv[1:3]\nfrom service import Gateway, GatewayRequest\nfrom registry import ConnectorRegistry, ConnectorCapability\nfrom knowledge_read_lab_registry import CAPABILITY, LAB_ENGINE_SCOPES, register_knowledge_lab_capabilities, knowledge_lab_policy\n\nrequest = GatewayRequest(**json.load(sys.stdin))\nregistry = ConnectorRegistry()\nregister_knowledge_lab_capabilities(registry=registry, connector_type=ConnectorCapability, enabled=True)\n\ndef probe_policy(req):\n    is_probe_read = req.capability == CAPABILITY and req.environment == \"LAB\"\n    return is_probe_read, None if is_probe_read else \"POLICY_CONFLICT\"\n\ngateway = Gateway(set().union(*LAB_ENGINE_SCOPES.values()), registry, knowledge_lab_policy(probe_policy))\nprint(json.dumps(gateway.route(request)))\n";
function routeGateway(request) {
  return JSON.parse(execFileSync('python3', ['-c', PYTHON_ROUTE,
    resolve(__dirname,'../../gateway'), resolve(__dirname,'../../connectors')], {
    input:JSON.stringify(request), encoding:'utf8', stdio:['pipe','pipe','ignore'], timeout:5000,
  }));
}
let tokenPromise;
function googleAccessToken({service_account_email, requested_scope, environment}) {
  if (service_account_email !== serviceAccount || requested_scope !== REQUIRED_SCOPE || environment !== 'LAB') throw new Error('PROBE_TOKEN_SCOPE_DENIED');
  tokenPromise ??= (async () => {
    const operatorToken = gcloud('auth','print-access-token','--quiet');
    const response = await fetch('https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/' + serviceAccount + ':generateAccessToken', {
      method:'POST', redirect:'error', signal:AbortSignal.timeout(15000),
      headers:{Authorization:'Bearer '+operatorToken,'Content-Type':'application/json'},
      body:JSON.stringify({scope:[requested_scope], lifetime:'600s'}),
    });
    if (!response.ok) throw new Error('GOOGLE_IMPERSONATION_HTTP_' + response.status);
    return (await response.json()).accessToken;
  })();
  return tokenPromise;
}
let googleCalls = 0;
let fault = '';
let auditCount = 0;
const reader = createLabGatewayKnowledgeCapability({
  enabled: process.env.CEREBRO_KNOWLEDGE_PRIVATE_PROBE === '1',
  authenticateRuntime,
  readTrustedGrants: principal => principal.id === 'cloud-shell-operator-probe' ? grants : [],
  routeGateway,
  policyCheck,
  googleAccessToken: args => {
    if (fault === 'credential') throw new Error('PROBE_CREDENTIAL_UNAVAILABLE');
    return googleAccessToken(args);
  },
  persistAudit: event => {
    if (fault === 'audit') throw new Error('PROBE_AUDIT_UNAVAILABLE');
    appendFileSync(auditPath, JSON.stringify({...event, probe_fault:fault || undefined})+'\n', {mode:0o600});
    auditCount++;
  },
  fetchImpl: async (url, options) => {
    googleCalls++;
    if (fault === 'google') return {ok:false,status:503};
    const response = await fetch(url, options);
    if (fault !== 'hash' || !response.ok) return response;
    // A real response is copied and altered only in memory for this negative.
    const data = await response.json();
    const deliveries = data.valueRanges.find(item => item.range.includes('Entregas_LAB'));
    let altered = 0;
    for (const row of deliveries?.values ?? []) {
      if (row[1] === grants[0].company_id && row[3] === grants[0].subagent_id) {
        row[5] = '0'.repeat(64);
        altered++;
      }
    }
    if (!altered) throw new Error('PROBE_HASH_TARGET_MISSING');
    return {ok:true,json:async()=>data};
  },
});

async function main() {
  if (reader.status === 'DISABLED_LAB') {
    await assert.rejects(reader.read(caller,grants[0]),/KNOWLEDGE_LAB_BINDING_DISABLED/);
    assert.equal(googleCalls,0);
    console.log('PROBE_DISABLED_NO_GOOGLE');
    return;
  }
  const denied = [
    ['unauthenticated', null, grants[0], /GATEWAY_LAB_RUNTIME_IDENTITY_NOT_VERIFIED/],
    ['foreign_company', caller, {...grants[0],company_id:'other-company'}, /SCOPE_DENIED/],
    ['wrong_version', caller, {...grants[0],version:'other-version'}, /SCOPE_DENIED/],
    ['unauthorized_specialist', caller, {...grants[0],subagent_id:'FB-00.SA-999'}, /SCOPE_DENIED/],
  ];
  for (const [name,context,request,error] of denied) {
    await assert.rejects(reader.read(context,request),error);
    console.log(JSON.stringify({check:name,result:'DENIED'}));
  }
  assert.equal(googleCalls,0);
  const reads=[];
  for (const request of grants) {
    try {
      const r=await reader.read(caller,request);
      reads.push(request.department_id);
      console.log(JSON.stringify({department:request.department_id,status:'READ_VERIFIED',sha256:r.sha256}));
    } catch (error) {
      if (error.message !== 'DELIVERY_RECEIPT_PENDING') throw error;
      console.log(JSON.stringify({department:request.department_id,status:'PENDING_RECEIPT'}));
    }
  }
  const checks = [
    ['hash', /DELIVERY_RECEIPT_PENDING/],
    ['credential', /PROBE_CREDENTIAL_UNAVAILABLE/],
    ['google', /GOOGLE_SHEETS_HTTP_503/],
    ['audit', /PROBE_AUDIT_UNAVAILABLE/],
  ];
  for (const [name, error] of checks) {
    fault=name;
    await assert.rejects(reader.read(caller,grants[0]),error);
    console.log(JSON.stringify({check:name,result:'FAIL_CLOSED',fault_injected:true}));
  }
  fault='';
  const recovered=await reader.read(caller,grants[0]);
  assert.match(recovered.sha256,/^[0-9a-f]{64}$/);
  console.log(JSON.stringify({verified_reads:reads.length,departments:reads,audit_records:auditCount,recovered:true,google_requests:googleCalls,execution:'TEMPORARY_CLOUD_SHELL_PROBE',agent_consumption:0}));
  if (reads.length < 3) process.exitCode=2;
}
main().catch(error=>{
  console.error(/^[A-Z0-9_]+$/.test(error.message) ? error.message : 'PRIVATE_BINDING_PROBE_FAILED');
  process.exitCode=1;
});

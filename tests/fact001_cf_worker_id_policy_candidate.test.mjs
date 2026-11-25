import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
import {isCanonicalEngineId,patchFactLabWorkerIdPolicy} from '../cerebro-os/factory/cf_fact_lab_worker_id_policy_candidate.mjs';

const here=dirname(fileURLToPath(import.meta.url));
const canonical=JSON.parse(readFileSync(resolve(here,'../cerebro-os/registry/canonical_177.json'),'utf8')).engine_ids;
const seed=JSON.parse(readFileSync(resolve(here,'../cerebro-os/registry/engine_registry.seed.json'),'utf8'));
const bridge='cerebro-fact001-github-oidc-enroll-lab-eu';
const provisioner='cerebro-fact001-ums001-issuer-provisioner-lab-eu';
const pad='// FACT001_ENGINE_CREATED OIDC_BRIDGE_ENABLED FACT_EVENT_SIGNATURE_DENIED\n'.repeat(4);
const source=(which)=>which===bridge
 ? pad+'const rxEngine=/^[A-Z][A-Z0-9-]{2,63}$/;\n'+pad
 : pad+'const id=/^[A-Z][A-Z0-9-]{2,63}$/;\n'+pad;

test('all 177 canonic engines and 13 seed entries remain accepted',()=>{
 assert.equal(canonical.length,177);
 assert.equal(seed.length,13);
 for(const value of canonical.concat(seed.map(x=>x.engine_id)))assert.equal(isCanonicalEngineId(value),true,value);
});

test('invalid identifiers cannot pass canonical validation',()=>{
 for(const value of ['---','999','A--','-FACT','FACT-','AB','../../../secret','A_B',''])assert.equal(isCanonicalEngineId(value),false,value);
});

test('provisioner patch changes only its deployed regex anchor',()=>{
 const old=source(provisioner);
 const r=patchFactLabWorkerIdPolicy(provisioner,old);
 assert.equal(r.worker_name,provisioner);
 assert.equal(r.deploy_authorized,false);
 assert.equal(r.requires_signed_runtime_identity,true);
 assert.equal(r.cloudflare_customer_cost_measured,false);
 assert.equal(r.source.replace(r.new_policy,r.old_policy),old);
 assert.match(r.source,/\(\?=\.\{3,64\}\$\)/);
});

test('OIDC bridge patch retains existing auth and replay checks',()=>{
 const old=source(bridge);
 const r=patchFactLabWorkerIdPolicy(bridge,old);
 assert.equal(r.deploy_authorized,false);
 assert.equal(r.source.replace(r.new_policy,r.old_policy),old);
 assert.ok(r.source.includes('OIDC_BRIDGE_ENABLED'));
});

test('unknown worker, drifted source and missing verification fail closed',()=>{
 assert.throws(()=>patchFactLabWorkerIdPolicy('production-worker',source(bridge)),/DENIED/);
 assert.throws(()=>patchFactLabWorkerIdPolicy(bridge,source(bridge).replace('rxEngine=/','rxEngine2=/')),/ANCHOR_DRIFT/);
 assert.throws(()=>patchFactLabWorkerIdPolicy(bridge,'abc'),/DENIED/);
 assert.throws(()=>patchFactLabWorkerIdPolicy(provisioner,'x'.repeat(200)),/NOT_VERIFIED/);
});

test('double application cannot silently overwrite deployed policy',()=>{
 const first=patchFactLabWorkerIdPolicy(provisioner,source(provisioner));
 assert.throws(()=>patchFactLabWorkerIdPolicy(provisioner,first.source),/ANCHOR_DRIFT/);
});

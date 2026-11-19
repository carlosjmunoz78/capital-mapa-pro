import test from "node:test";
import assert from "node:assert/strict";
import {
  OBSERVED_STRICT_WORKERS_V1,
  auditFactCloudIdChain,
  auditCompanyScope
} from "../cerebro-os/factory/fact001_full_cloud_id_chain_preflight.mjs";

const OLD="/^[A-Z][A-Z0-9-]{2,63}$/";
const sample=(worker,count)=>({
  worker,
  code: "// LAB-ONLY FACT/UMS existing Worker source metadata\n" +
    ("if (!" + OLD + ".test(engineId)) throw Error('INVALID_ENGINE');\n").repeat(count) +
    "export default {async fetch(){return new Response('Not Found',{status:404})}};\n"
});
const sources=()=>Object.fromEntries(Object.entries(OBSERVED_STRICT_WORKERS_V1)
 .map(([worker,count])=>[worker,sample(worker,count).code]));

test("eight workers and 13 strict source locations must be audited",()=>{
 const report=auditFactCloudIdChain(sources());
 assert.equal(report.worker_count,8);
 assert.equal(report.strict_validator_sites,13);
 assert.equal(report.status,"SOURCE_CONTRACT_AUDITED_NOT_DEPLOYABLE");
 assert.equal(report.safe_to_promote,false);
 assert.equal(report.canonical_digit_leading_compatible,false);
 assert.equal(report.partial_two_worker_update_forbidden,true);
 assert.equal(report.signed_runtime_enrollment_proven_without_github_actions,false);
});

test("two-worker-only migration cannot pass full-chain gate",()=>{
 const partial=sources();
 for(const key of Object.keys(partial).slice(2))delete partial[key];
 assert.throws(()=>auditFactCloudIdChain(partial),/SCOPE_OR_SOURCE_MISSING/);
});

test("strict source drift, missing and substituted Workers fail closed",()=>{
 for(const worker of Object.keys(sources())){
  const altered=sources();
  altered[worker]=altered[worker].replace(OLD,"/^(?=.{3,64}$)(?=.*[A-Z])[A-Z0-9]+(?:-[A-Z0-9]+)*$/");
  assert.throws(()=>auditFactCloudIdChain(altered),/VALIDATOR_DRIFT/);
 }
 const swapped=sources();swapped["cerebro-unknown-prod"]=swapped[Object.keys(swapped)[0]];
 assert.throws(()=>auditFactCloudIdChain(swapped),/SCOPE_OR_SOURCE_MISSING/);
});

test("canonical company must not be normalized from legal name",()=>{
 const blocked=auditCompanyScope("fenix","fenix-capital");
 assert.equal(blocked.status,"HOLD_COMPANY_ID_MISMATCH");
 assert.equal(blocked.attribution_to_registry_allowed,false);
 assert.equal(blocked.aliases_automatically_assumed,false);
 assert.equal(blocked.needs_explicit_verified_alias_contract,true);
});

test("same company id only validates ID alignment, not action permissions",()=>{
 const check=auditCompanyScope("fenix","fenix");
 assert.equal(check.status,"SAME_CANONICAL_COMPANY_ID");
 assert.equal(check.attribution_to_registry_allowed,true);
 assert.equal(check.cross_company_action_allowed,false);
});

test("invalid company identity fails closed",()=>{
 for(const bad of ["FENIX","fenix capital","","../fenix"]){
  assert.throws(()=>auditCompanyScope("fenix",bad),/FACT_COMPANY_SCOPE_INVALID/);
 }
});

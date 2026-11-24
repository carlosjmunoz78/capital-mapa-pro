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

import {planClassifiedCloudIdChainMigration,CANONICAL_ENGINE_RULE_CP141} from '../cerebro-os/factory/fact001_full_cloud_id_chain_preflight.mjs';
import {readFileSync} from 'node:fs';
const [fact,bridge,provisioner,executor,adapter,gateway,router,broker]=Object.keys(OBSERVED_STRICT_WORKERS_V1);
const binding='issuer.origin_engine_id!==e.issuer||issuer.origin_engine_id!==r.origin_engine_id';
const inline=arg=>OLD+'.test('+arg+')';
const named=(name,args)=>'const '+name+'='+OLD+';\n'+args.map(x=>name+'.test('+x+');').join('\n');
const shared=named('id',["r.origin_engine_id||''","r.consumer_engine_id||''","r.origin_engine_id","e.issuer||''"])+ '\nif('+binding+')throw Error("UNTRUSTED_ISSUER");';
const fixture=()=>Object.fromEntries(Object.entries({
 [fact]:[inline('engineId'),inline('runtimeId'),inline("engineId||''")].join(';'),
 [bridge]:named('rxEngine',['engine',"body.engine_id||''","body.engine_id||''","input.engine_id||''"]),
 [provisioner]:named('id',["e.engine_id||''","msg.engine_id||''","input.engine_id||''","input.engine_id||''","payload.engine_id||''","engine_id||''","input.engine_id||''","engine_id||''"]),
 [executor]:named('engineRx',["r.origin_engine_id||''"]),[adapter]:shared,
 [gateway]:shared+';'+inline("i.origin_engine_id||''")+';'+inline("r.origin_engine_id||''"),
 [router]:inline("r.origin_engine_id||''")+';'+inline("r.consumer_engine_id||''"),[broker]:named('ID',["principal.engine_id||''"])
}).map(([k,v])=>[k,'// fixture for existing Worker source shape\n'+v+'\n// preserves other source bytes and contains no secrets\n']));
test('full classified plan transforms 12 engine validators but keeps runtime validator and issuer binding',()=>{
 const original=fixture(),p=planClassifiedCloudIdChainMigration(original);
 assert.equal(p.engine_validator_sites_changed,12);assert.equal(p.runtime_validator_sites_preserved,1);assert.equal(p.workers.length,8);assert.equal(p.deploy_authorized,false);assert.equal(p.safe_to_promote,false);
 assert.ok(p.source_candidates[fact].includes(OLD+'.test(runtimeId)'));
 for(const w of [adapter,gateway])assert.ok(p.source_candidates[w].includes(binding));
 for(const w of p.workers)assert.equal(w.exact_roundtrip,true);
 assert.equal(Object.values(original).join('').split(OLD).length-1,13);
});
test('all 177 canonical IDs pass the candidate while malformed IDs remain rejected',()=>{
 const rx=new RegExp(CANONICAL_ENGINE_RULE_CP141.slice(1,-1));
 const ids=JSON.parse(readFileSync(new URL('../cerebro-os/registry/canonical_177.json',import.meta.url),'utf8')).engine_ids;
 assert.equal(ids.length,177);for(const id of ids)assert.ok(rx.test(id),id);assert.ok(rx.test('3RD-001'));for(const id of ['---','999','A--','-FACT','FACT-','AB','../SECRET','A_B',''])assert.equal(rx.test(id),false,id);
});
test('unknown engine validator field fails closed even when regex count unchanged',()=>{const f=fixture();f[fact]=f[fact].replace('test(engineId)','test(runtimeId2)');assert.throws(()=>planClassifiedCloudIdChainMigration(f),/ANCHOR_DRIFT/);});
test('shared issuer validator requires original engine equality checks',()=>{for(const w of [adapter,gateway]){const f=fixture();f[w]=f[w].replace(binding,'issuer.enabled===1');assert.throws(()=>planClassifiedCloudIdChainMigration(f),/ANCHOR_DRIFT/);}});
test('new named validator consumer and changed runtime field both fail closed',()=>{const f=fixture();f[broker]+=';ID.test(runtime_id);';assert.throws(()=>planClassifiedCloudIdChainMigration(f),/USAGE_DRIFT/);const g=fixture();g[fact]=g[fact].replace('test(runtimeId)','test(otherId)');assert.throws(()=>planClassifiedCloudIdChainMigration(g),/ANCHOR_DRIFT/);});
test('reapplying source-only candidate is denied',()=>assert.throws(()=>planClassifiedCloudIdChainMigration(planClassifiedCloudIdChainMigration(fixture()).source_candidates),/VALIDATOR_DRIFT/));

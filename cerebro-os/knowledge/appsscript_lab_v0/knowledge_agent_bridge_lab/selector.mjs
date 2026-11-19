/** SOC-FB FB-00.SA-001 Company Selector deterministic SHADOW V1.
 * No network, DB, AI, write, publication or certification.
 * gateway fixture is synthetic. Real Gateway crypto verification is NOT implemented.
 */
export const VERSION="1.0.0";
const ACT=new Set(["READ_CONTEXT","DRAFT_CONTENT"]);
const id=x=>typeof x==="string"&&/^[a-z][a-z0-9-]{1,79}$/.test(x);
const text=x=>typeof x==="string"&&x.length>0&&x.length<=120;
function result(state,reason,extra={}){
 return Object.freeze({version:VERSION,company_id:"fenix-capital",environment:"LAB",
 engine_id:"SOC-FB-FINANCIAL-REAL-ESTATE-V1",component_id:"FB-00.SA-001",
 state,reason,mode:"SHADOW_ONLY",certification:"NOT_CERTIFIED",
 gateway_production_authority:"NOT_IMPLEMENTED",may_publish:false,may_send_message:false,
 may_spend:false,may_write_crm:false,external_actions:0,...extra});
}
export function runCompanySelector({gateway,registry,request}={},verifiedRead){
 if(!verifiedRead || verifiedRead.bundle?.subagent_id!=="FB-00.SA-001" ||
   !verifiedRead.bundle.items?.some(x=>x.knowledge_id==="RULE:K-SCOPE"&&x.payload?.id==="K-SCOPE") ||
   !verifiedRead.bundle.items.some(x=>x.knowledge_id==="RULE:K-TERRITORY"&&x.payload?.id==="K-TERRITORY"))
  return result("HOLD_KNOWLEDGE_RULES","Required authenticated rules missing");
 const fail=(s,r)=>result(s,r);
 if(!gateway||!registry||!request||gateway.attested!==true||
 gateway.trust_source!=="AUTHENTICATED_KNOWLEDGE_READ")
 return fail("HOLD_GATEWAY_PROOF","Missing authenticated LAB Gateway context");
 if([gateway.environment,registry.environment,request.environment].some(v=>v!=="LAB"))
 return fail("HOLD_ENVIRONMENT","LAB-only");
 const g=gateway.company_id,r=registry.company_id,q=request.company_id;
 if(!id(g)||!id(r)||!id(q)||g!=="fenix-capital")
 return fail("HOLD_COMPANY_ID","Unknown or unauthorized tenant");
 if(g!==r||g!==q||registry.active!==true||registry.verified!==true)
 return fail("BLOCK_TENANT_MISMATCH","Authenticated tenant, request and registry must match");
 if(!ACT.has(request.action))return fail("BLOCK_NON_DRAFT_ACTION","No external actions");
 if(!Array.isArray(gateway.permissions)||!gateway.permissions.includes(request.action))
 return fail("BLOCK_MISSING_PERMISSION","Missing precise action scope");
 const asset=request.asset_id;
 if(!id(asset)||!Array.isArray(registry.assets)||
 !registry.assets.some(a=>a?.asset_id===asset&&a.company_id===g&&a.active===true)||
 !Array.isArray(gateway.asset_scopes)||!gateway.asset_scopes.includes(asset))
 return fail("BLOCK_ASSET_SCOPE","Asset must belong to the selected tenant");
 if(request.source_company_id&&request.source_company_id!==g||
 request.source_type==="private_other_company")
 return fail("BLOCK_CROSS_COMPANY_DATA","No transfer of another company's private information");
 if(["claimed_grant","override_permission","debug_bypass"].some(k=>Object.hasOwn(request,k)))
 return fail("BLOCK_UNTRUSTED_OVERRIDE","User-supplied grants are ignored");
 const t=request.territory;
 if(!t||!text(t.country)||!text(t.province)||!text(t.municipality)||
 t.zone!==undefined&&!text(t.zone))
 return fail("HOLD_TERRITORY_GRAIN","Country/province/municipality must be independently specified");
 if(request.market_data&&!request.market_data.granularity)
 return fail("HOLD_MARKET_GRAIN","Unknown data granularity");
 if(request.market_data?.granularity==="province"&&request.market_data.asserts_zone_fact===true)
 return fail("BLOCK_GEOGRAPHIC_INFERENCE","Province data cannot infer neighborhood facts");
 if(request.persona!==undefined&&!text(request.persona))
 return fail("HOLD_PERSONA","Persona must be a bounded hypothesis");
 if(request.claims_credit_approval===true||request.claims_approval_rate_without_evidence===true)
 return fail("BLOCK_UNVERIFIED_CREDIT_CLAIM","No unverifiable mortgage claims");
 if(["OUTDATED","UNKNOWN","NOT_VERIFIED"].includes(request.source_freshness))
 return fail("HOLD_SOURCE_FRESHNESS","Reverify stale or unknown primary source");
 return result("SHADOW_ELIGIBLE_FOR_READ_OR_DRAFT","Scoped real knowledge context passed all LAB gates",{
 simulated_action:request.action,selected_company_id:g,asset_id:asset,
 territory:{country:t.country,province:t.province,municipality:t.municipality,
 ...(t.zone?{zone:t.zone}:{})},
 buyer_persona_hypothesis:request.persona??null,
 production_authority:false});
}

// CEREBRO OS UMS-001: pure visual analysis validator, LAB ONLY.
// A model's opinion is advisory until independent calibration and dual review.
export const MODEL = "@cf/meta/llama-3.2-11b-vision-instruct";
export const REQUIRED = Object.freeze([
  "connected_limbs", "realistic_hands", "realistic_faces", "no_fake_text",
  "physical_coherence", "scene_matches_brief", "professional_quality"
]);
export const KNOWN_REJECTED = Object.freeze({
  "6b4b1596ec87efd30f4d7ac677e19514a10f6896b22587dddcec06a23c8c2791": "ANATOMY_DISCONNECTED_LIMBS",
  "c227a0723d89a2ff8292d709bd171aa617a8cfb27dbeb64ea508df23c87dfc18": "UNREADABLE_SYNTHETIC_TEXT"
});
export const INSPECT_PROMPT = [
  "You are a strict professional photo quality controller, NOT a creative writer.",
  "Inspect the ACTUAL image attached, do not assume the prompt was followed.",
  "Check whether the arms/hands are correctly attached to bodies, fingers and faces",
  "are plausible, screens and papers have no fake letters/numbers or gibberish,",
  "objects have natural geometry, and scene matches a premium mortgage newsletter.",
  "When not fully certain, set check false. Be severe with AI-generated anatomy.",
  'Return ONLY JSON: {"connected_limbs":true,"realistic_hands":true,',
  '"realistic_faces":true,"no_fake_text":true,"physical_coherence":true,',
  '"scene_matches_brief":true,"professional_quality":true,',
  '"confidence":0.0,"findings":["specific objective defect"]}.',
  "No explanations outside JSON. Confidence 0..1 is uncalibrated.",
].join(" ");
const HOLD=(reason)=>({status:"QA_HOLD",reason, reuse_allowed:false,publish_authorized:false,independent_vision_verified:false});
const REJECT=(reasons)=>({status:"REJECTED_VISUAL",reasons,reuse_allowed:false,publish_authorized:false,independent_vision_verified:false});
export function parseModelResult(raw) {
  const value=raw?.response??raw?.result?.response??raw?.choices?.[0]?.message?.content??raw;
  if(typeof value!=="string"||value.length>9000)return null;
  try{
    const obj=JSON.parse(value.trim());
    if(!obj||Array.isArray(obj)||typeof obj!=="object")return null;
    const keys=Object.keys(obj).sort();
    const expected=[...REQUIRED,"confidence","findings"].sort();
    if(keys.length!==expected.length||keys.some((x,i)=>x!==expected[i]))return null;
    if(REQUIRED.some(key=>typeof obj[key]!=="boolean"))return null;
    if(typeof obj.confidence!=="number"||!Number.isFinite(obj.confidence)||obj.confidence<0||obj.confidence>1)return null;
    if(!Array.isArray(obj.findings)||obj.findings.length>8||obj.findings.some(x=>typeof x!=="string"||x.length>180))return null;
    return obj;
  }catch{return null;}
}
export function verdict({asset_sha256,company_id,engine_id,request_id,environment,modelOutput,providerCalled=false}) {
  if(typeof asset_sha256!=="string"||!/^[a-f0-9]{64}$/.test(asset_sha256)
    ||typeof company_id!=="string"||!company_id||typeof engine_id!=="string"||!engine_id
    ||typeof request_id!=="string"||!request_id||environment!=="LAB")return HOLD("INVALID_ASSET_SCOPE");
  if(Object.hasOwn(KNOWN_REJECTED,asset_sha256))return REJECT([KNOWN_REJECTED[asset_sha256]]);
  if(!providerCalled)return HOLD("VISION_MODEL_NOT_RUN");
  const review=parseModelResult(modelOutput);
  if(!review)return HOLD("MODEL_RESPONSE_INVALID");
  const failures=REQUIRED.filter(k=>review[k]!==true);
  if(failures.length)return REJECT(failures.map(k=>"VISION_"+k.toUpperCase()));
  if(review.confidence<0.95||review.findings.length) return HOLD("UNCERTAIN_VISION");
  // Single multimodal model is not independent calibrated proof. Never auto-promote.
  return {status:"QA_CANDIDATE_UNCALIBRATED",confidence_reported:review.confidence,
    model:MODEL,reuse_allowed:false,publish_authorized:false,independent_vision_verified:false};
}
export async function inspect({env,asset_sha256,company_id,engine_id,request_id,environment,imageBytes}) {
  const common={asset_sha256,company_id,engine_id,request_id,environment};
  const prior=verdict({...common});
  if(prior.status==="REJECTED_VISUAL"||prior.reason==="INVALID_ASSET_SCOPE")return prior;
  if(!env||env.VISION_QA_ENABLED!=="true"||env.VISION_QA_COST_VERIFIED!=="true")
    return HOLD("VISION_DISABLED_OR_BUDGET_UNVERIFIED");
  if(!env.AI||typeof env.AI.run!=="function"||!(imageBytes instanceof Uint8Array)
     ||imageBytes.length<4000||imageBytes.length>4500000)return HOLD("VISION_INPUT_UNAVAILABLE");
  try{
    const raw=await env.AI.run(MODEL,{
      prompt:INSPECT_PROMPT,image:[...imageBytes],max_tokens:320,temperature:0
    });
    return verdict({...common,modelOutput:raw,providerCalled:true});
  }catch{return HOLD("VISION_PROVIDER_FAILED");}
}

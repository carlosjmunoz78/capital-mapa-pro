/**
 * FACT-001 / CEREBRO Model Router · DeepSeek shared API credential, LAB.
 * One account-level Secrets Store binding. No direct public route or cron.
 * Read-only balance probe is optional; inference NEVER enabled in this revision.
 *
 * Access ONLY via explicit Cloudflare Service Bindings from audited consumers.
 * Identity in payload is an additional policy gate, not caller authentication.
 */
const COMPANY = "fenix-capital";
const EXPECTED = new Map([
  ["SOC-FB-FINANCIAL-REAL-ESTATE-V1", "FACEBOOK"],
  ["SOC-IG-FINANCIAL-REAL-ESTATE-V1", "INSTAGRAM"],
  ["SOC-LI-FINANCIAL-REAL-ESTATE-V1", "LINKEDIN"],
  ["SOC-001", "SOC-ORCHESTRATOR"]
]);
const ALLOWED_MODELS = ["deepseek-flash", "deepseek-v4-pro"];
const SECRET_ID = "CEREBRO_OS_SHARED_DEEPSEEK_V1";

const reply = (value, status=200) => new Response(JSON.stringify(value),{
  status,headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"}
});
const deny=(reason,status=423)=>reply({state:"HOLD",reason,provider_call:false,model_tokens:0,publish_authorized:false},status);
const valid=(b)=>b&&b.company_id===COMPANY&&
 typeof b.engine_id==="string"&&EXPECTED.has(b.engine_id)&&
 b.environment==="LAB"&&typeof b.version==="string"&&/^[0-9]+\.[0-9]+\.[0-9]+$/.test(b.version);

export default {
 async fetch(request,env) {
  if(env.ROUTER_ENABLED!=="true")return deny("ROUTER_DISABLED",503);
  if(request.method!=="POST")return deny("METHOD_NOT_ALLOWED",405);
  let u;try{u=new URL(request.url)}catch{return deny("BAD_URL",400)}
  const path=u.pathname;
  if(!["/v1/status","/v1/readonly-balance","/v1/infer"].includes(path))
     return deny("NOT_FOUND",404);
  const type=request.headers.get("content-type")||"";
  if(!type.startsWith("application/json"))return deny("JSON_REQUIRED",415);
  let body;try{body=await request.json()}catch{return deny("INVALID_BODY",400)}
  if(!valid(body))return deny("ENGINE_NOT_ALLOWED",403);
  const common={company_id:COMPANY,engine_id:body.engine_id,environment:"LAB",
    version:"0.1.0",provider:"deepseek",shared_credential_name:SECRET_ID,
    supported_models:ALLOWED_MODELS,public_endpoint:false,secret_value_returned:false};
  if(path==="/v1/status"){
    return reply({...common,state:"AVAILABLE_CONFIGURED_NOT_INFERENCE",
      secret_binding_present:!!env.SHARED_DEEPSEEK_SECRET,
      infer_enabled:false,readonly_probe_enabled:env.READONLY_BALANCE_PROBE_ENABLED==="true",
      approved_zero_spend:true,auto_topup_enabled:false});
  }
  if(path==="/v1/infer"){
    // There is deliberately no API inference code in the LAB broker.
    // Any future enabled release requires preverified enforceable spending controls.
    return deny("PAYMENT_AND_POLICY_GATES_REQUIRED");
  }
  if(env.READONLY_BALANCE_PROBE_ENABLED!=="true")return deny("READONLY_PROBE_DISABLED");
  if(!env.SHARED_DEEPSEEK_SECRET||typeof env.SHARED_DEEPSEEK_SECRET.get!=="function")
    return deny("SECRET_BINDING_UNAVAILABLE",503);
  let key;
  try{key=await env.SHARED_DEEPSEEK_SECRET.get()}catch{return deny("SECRET_READ_UNAVAILABLE",503)}
  if(typeof key!=="string"||!key.startsWith("sk-")||key.length<20)return deny("SECRET_INVALID",503);
  // Non-billable DeepSeek account balance API; no model inference.
  let result;
  try{
    const response=await fetch("https://api.deepseek.com/user/balance",{
      method:"GET",headers:{Authorization:"Bearer "+key,Accept:"application/json"},
      redirect:"error",signal:AbortSignal.timeout(10000)});
    if(response.status!==200)
      return reply({...common,state:"ACCOUNT_AUTH_PROBE_FAILED",http_status:response.status,
        credentials_exposed:false,model_calls:0},503);
    result=await response.json();
  }catch{return reply({...common,state:"ACCOUNT_PROBE_NETWORK_ERROR",model_calls:0},503)}
  const validBalance=typeof result?.is_available==="boolean";
  if(!validBalance)return deny("BALANCE_RESPONSE_INVALID",503);
  // No balances/amounts/keys/user details exposed to the calling Worker.
  return reply({...common,state:"ACCOUNT_AUTHENTICATED_READONLY",account_api_auth_valid:true,
    balance_available:result.is_available,model_calls:0,estimated_added_cost_eur:0,
    grant_and_topup_hard_stop_verified:false,
    inference_status:"BLOCKED",
    message:"Authentication success does NOT authorize any paid model call."});
 }
};

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
// Owner directive 2026-11-13: DeepSeek is a LIMITED supplementary learning tool.
// Future inference implementation MUST implement persistent, atomic daily counters
// and a billing hard stop BEFORE enabling any provider/model request.
const LEARNING_POLICY = Object.freeze({
 purpose:"shadow_learning_and_targeted_remediation_only",
 priority:"deterministic_then_existing_free_models_then_deepseek",
 max_requests_per_engine_per_utc_day:2,
 max_requests_across_engines_per_utc_day:6,
 max_output_tokens_per_request:512,
 automatic_retry_count:0,
 bulk_batches_allowed:false,
 direct_publishing_allowed:false,
 seo_enabled:false,
 default_spending_limit_eur_per_day:0,
 requires_verified_provider_credit_and_hard_spend_cap:true,
 requires_persistent_atomic_global_and_engine_counters:true,
 permits_paid_inference_without_explicit_budget:false
});

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
  if(!["/v1/status","/v1/readonly-balance","/v1/budget-status","/v1/infer"].includes(path))
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
      approved_zero_spend:true,auto_topup_enabled:false,learning_policy:LEARNING_POLICY});
  }
  if(path==="/v1/budget-status"){
    if(!env.BUDGET_LEDGER)return deny("BUDGET_BINDING_MISSING",503);
    try{
      const state=await env.BUDGET_LEDGER.getByName("cerebro-os-shared-budget-global").status();
      return reply({...common,state:"BUDGET_LEDGER_CONNECTED",ledger:{
        date:state.date,monthly_reserved_cents:state.month_reserved_cents,
        global_daily_calls:state.day?.global_calls||0,
        global_daily_max:state.global_quota_per_day,
        per_engine_daily_max:state.engine_quota_per_day,
        monthly_reserved_max_cents:state.max_reserved_month_cents
      },inference_enabled:false});
    }catch{return deny("BUDGET_LEDGER_NOT_READY",503);}
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


/**
 * CEREBRO OS · single shared Cloudflare SQLite Durable Object budget ledger.
 * Atomic reserve-before-request; no refunds or retries. No API secrets.
 * LAB only. Never call a provider when a reservation is denied or uncertain.
 */
export class SharedBudgetLedger {
 constructor(ctx,env){this.ctx=ctx;this.env=env;}
 async reserve(input){
  const allow=new Set(["SOC-LI-FINANCIAL-REAL-ESTATE-V1","SOC-FB-FINANCIAL-REAL-ESTATE-V1","SOC-IG-FINANCIAL-REAL-ESTATE-V1","SOC-001"]);
  if(!input||input.company_id!=="fenix-capital"||input.environment!=="LAB"||
     !allow.has(input.engine_id)||input.seo===true||
     typeof input.request_id!=="string"||!/^li-[a-z0-9_-]{8,100}$/i.test(input.request_id))
    return{state:"HOLD_IDENTITY",granted:false};
  if(input.cloudflare_exhausted_verified!==true||input.provider_balance_verified!==true||
     input.auto_topup_off_verified!==true||input.price_ceiling_verified!==true||
     input.paid_calls_authorized!==true||input.hard_invoice_cap_verified!==true||
     !Number.isSafeInteger(input.input_tokens_max)||!Number.isSafeInteger(input.output_tokens_max)||
     input.input_tokens_max>1200||input.output_tokens_max>512||
     input.input_tokens_max<1||input.output_tokens_max<1)
    return{state:"HOLD_FALLBACK_POLICY",granted:false};
  const d=new Date().toISOString().slice(0,10),month=d.slice(0,7),request=input.request_id;
  return this.ctx.storage.transactionSync(()=>{
   const kv=this.ctx.storage.kv,known=kv.get("request:"+request);
   if(known)return{state:"DUPLICATE_RESERVATION",granted:false};
   const day=kv.get("day:"+d)||{global_calls:0,per_engine:{},reserved_cents:0};
   const mon=kv.get("month:"+month)||{reserved_cents:0};
   const engineCalls=day.per_engine[input.engine_id]||0;
   // 1 euro cent reserved per request, conservative at externally verified pricing.
   // Maximum €0.06 per UTC day and €0.50 per month across all consumers.
   if(day.global_calls>=6||engineCalls>=2||day.reserved_cents+1>6||
      mon.reserved_cents+1>50)
     return{state:"HOLD_SPENDING_LIMIT",granted:false};
   day.global_calls++;day.per_engine[input.engine_id]=engineCalls+1;
   day.reserved_cents++;mon.reserved_cents++;
   kv.put("day:"+d,day);kv.put("month:"+month,mon);
   kv.put("request:"+request,{company_id:input.company_id,engine_id:input.engine_id,
      day:d,month,at:new Date().toISOString(),reserve_cents:1,
      state:"RESERVED_NO_RETRY",paid_call_sent:false});
   return{state:"RESERVED_ATOMIC",granted:true,reservation_id:request,
     daily_global_remaining:6-day.global_calls,
     daily_engine_remaining:2-day.per_engine[input.engine_id],
     monthly_reserved_eur:mon.reserved_cents/100};
  });
 }
 async report({request_id,result}={}){
  if(!/^li-[a-z0-9_-]{8,100}$/i.test(request_id||"")||
     !["SUCCESS","PROVIDER_FAILED","UNKNOWN"].includes(result))
    return{state:"HOLD_REPORT_INVALID"};
  return this.ctx.storage.transactionSync(()=>{
   const kv=this.ctx.storage.kv,entry=kv.get("request:"+request_id);
   if(!entry)return{state:"HOLD_NO_RESERVATION"};
   if(entry.result)return{state:"ALREADY_REPORTED"};
   // Never refund on provider error: retains conservative maximum charge.
   kv.put("request:"+request_id,{...entry,result,reported_at:new Date().toISOString()});
   return{state:"REPORTED_NO_REFUND",result};
  });
 }
 async status(){
  const d=new Date().toISOString().slice(0,10),m=d.slice(0,7),kv=this.ctx.storage.kv;
  return{date:d,month:m,day:kv.get("day:"+d)||{global_calls:0,reserved_cents:0},
     month_reserved_cents:(kv.get("month:"+m)||{reserved_cents:0}).reserved_cents,
     engine_quota_per_day:2,global_quota_per_day:6,
     max_reserved_month_cents:50,paid_execution_authorized_by_this_status:false};
 }
}

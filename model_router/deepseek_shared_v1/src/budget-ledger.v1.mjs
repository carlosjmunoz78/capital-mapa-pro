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

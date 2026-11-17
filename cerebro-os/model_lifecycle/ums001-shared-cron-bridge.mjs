/**
 * FACT-001 · deterministic and reversible UMS-001 cron bridge patch.
 * Applied only to the existing LAB scheduled handler, never an unverified PROD Worker.
 */
export const OLD_SCHEDULED=[
 "async scheduled(controller,env,ctx){",
 "  if(controller.cron!==DAILY_CRON||env.SOURCE_REFRESH_SCHEDULE_ENABLED!=='true')return;",
 "  ctx.waitUntil(enqueueDailySourceRefresh(env,controller.cron));",
 " },"
].join("\n");
export const NEW_SCHEDULED=[
 "async scheduled(controller,env,ctx){",
 "  if(controller.cron!==DAILY_CRON)return;",
 "  if(env.SOURCE_REFRESH_SCHEDULE_ENABLED==='true')",
 "   ctx.waitUntil(enqueueDailySourceRefresh(env,controller.cron));",
 "  if(env.MODEL_LIFECYCLE_WATCH?.fetch){",
 "   const req=new Request('https://model-lifecycle.cerebro.internal/v0/internal/daily-model-watch',",
 "     {method:'POST',headers:{'x-cerebro-shared-scheduler':'FACT-001/SUP-001/LAB'}});",
 "   ctx.waitUntil(env.MODEL_LIFECYCLE_WATCH.fetch(req)",
 "     .then(r=>{if(!r.ok)console.log(JSON.stringify({event:'MODEL_WATCHER_BRIDGE_HOLD',status:r.status}));})",
 "     .catch(()=>console.log('MODEL_WATCHER_BRIDGE_ERROR')));",
 "  }",
 " },"
].join("\n");
export function applySharedCronBridge(source){
 if(typeof source!=="string"||source.split(OLD_SCHEDULED).length!==2||
    source.includes("MODEL_LIFECYCLE_WATCH"))throw Error("UMS_BRIDGE_ANCHOR_MISSING_OR_ALREADY_PATCHED");
 const out=source.replace(OLD_SCHEDULED,NEW_SCHEDULED);
 if(out.replace(NEW_SCHEDULED,OLD_SCHEDULED)!==source)throw Error("UMS_BRIDGE_NOT_REVERSIBLE");
 return out;
}
export function rollbackSharedCronBridge(source){
 if(typeof source!=="string"||source.split(NEW_SCHEDULED).length!==2)
  throw Error("UMS_BRIDGE_ROLLBACK_ANCHOR_MISSING");
 return source.replace(NEW_SCHEDULED,OLD_SCHEDULED);
}

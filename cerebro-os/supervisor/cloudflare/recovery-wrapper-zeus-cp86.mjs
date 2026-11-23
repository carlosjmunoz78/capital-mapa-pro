// CP86 recovery-wrapper.mjs candidate. Original recovery & P5 cron unchanged.
import recovery from './legacy-recovery.mjs';
import {scheduledP5} from './worker.mjs';
import {probeP5Egress} from './egress-probe.mjs';
import {superviseP5Daily} from './zeus-p5-monitor.mjs';

export default {
 async fetch(request,env,ctx) {
   return recovery.fetch(request,env,ctx);
 },
 async scheduled(controller,env,ctx) {
   // Preserve the exact prior recovery heartbeat, P5 and egress operations.
   // ZEUS only reads their data and inserts into its own additive journal.
   recovery.scheduled(controller,env,ctx);
   ctx.waitUntil(probeP5Egress(env).then(v=>{
     console.log('FACT001_P5_EGRESS='+v.status);
   }).catch(()=>{ console.log('FACT001_P5_EGRESS=RECONCILE'); }));
   ctx.waitUntil(scheduledP5(env,controller.scheduledTime).then(v=>{
     console.log('FACT001_P5_SCHEDULED='+v.status);
   }).catch(()=>{ console.log('FACT001_P5_SCHEDULED=RECONCILE'); }));
   ctx.waitUntil(superviseP5Daily(env,controller.scheduledTime).then(v=>{
     console.log('ZEUS_P5_HEALTH='+v.status+':'+(v.code||'NONE'));
   }).catch(()=>{ console.log('ZEUS_P5_HEALTH=OBSERVABILITY_ERROR'); }));
 }
};

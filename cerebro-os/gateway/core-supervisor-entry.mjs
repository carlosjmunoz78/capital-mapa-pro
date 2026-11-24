import {SupervisorWorkflow185 as Old,closed} from '../factory/cp185/worker.mjs';
import {superviseCompletedOrder} from './core-supervisor.mjs';
export {closed as default};
export class SupervisorWorkflow185 extends Old{
 async run(event,step){if(!/^core-supervise-20261124-00[1-8]$/.test(event.instanceId))return super.run(event,step);
 const id='CORE-ORDER-20261124-'+event.instanceId.slice(-3);if(event.payload!==undefined&&event.payload!==null&&event.payload!=='{}'&&!(typeof event.payload==='object'&&Object.keys(event.payload).length===0))throw Error('SUPERVISOR_PAYLOAD_DENIED');
 return step.do('independent terminal order supervision',{retries:{limit:0,delay:'1 second'},timeout:'30 seconds'},()=>superviseCompletedOrder(this.env,id));}
}

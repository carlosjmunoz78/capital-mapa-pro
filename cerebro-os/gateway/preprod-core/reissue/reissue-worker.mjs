import {WorkflowEntrypoint} from 'cloudflare:workers';
import {rehearse} from './reissue-core.mjs';
export default {fetch(){return new Response(null,{status:404,headers:{'cache-control':'no-store'}})}};
export class ReissueRehearsal extends WorkflowEntrypoint{
 async run(event,step){const raw=event.payload;const p=typeof raw==='string'?JSON.parse(raw):raw;if(!p||Object.keys(p).sort().join('|')!=='prior')throw Error('PAYLOAD_DENIED');return step.do('isolated identity lifecycle',{retries:{limit:0,delay:'1 second'},timeout:'30 seconds'},()=>rehearse(this.env,event.instanceId,p.prior));}
}

import {DurableObject,WorkflowEntrypoint} from 'cloudflare:workers';
import {restoreArchive,readArchive} from './archive-core.mjs';
export default {fetch(){return new Response(null,{status:404,headers:{'cache-control':'no-store'}})}};
const enabled=e=>{if(e.CP186_ENABLED!=='true')throw Error('CP186_DISABLED')};
export class RecoveryScratch183 extends DurableObject{
 constructor(ctx,e){super(ctx,e);this.ctx=ctx;this.e=e;}
 restoreArchive(xs){enabled(this.e);return restoreArchive(this.ctx.storage,xs,{IAM:this.e.IAM_PUBLIC,TRIBUNAL:this.e.TRIBUNAL_PUBLIC})}
 readArchive(){enabled(this.e);return readArchive(this.ctx.storage,{IAM:this.e.IAM_PUBLIC,TRIBUNAL:this.e.TRIBUNAL_PUBLIC})}
}
export class RecoveryWorkflow183 extends WorkflowEntrypoint{
 async run(event,step){enabled(this.env);if(!['cp186-archive-restore-001','cp186-archive-readback-001'].includes(event.instanceId))throw Error('INSTANCE_DENIED');return step.do('isolated signed archive recovery',{retries:{limit:0,delay:'1 second'},timeout:'30 seconds'},()=>{const ns=this.env.SCRATCH.jurisdiction('eu'),stub=ns.get(ns.idFromName('cp186-isolated-signed-archive'));if(event.instanceId==='cp186-archive-restore-001'){const p=typeof event.payload==='string'?JSON.parse(event.payload):event.payload;return stub.restoreArchive(p)}return stub.readArchive()});}
}

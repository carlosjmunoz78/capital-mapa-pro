import {WorkerEntrypoint} from "cloudflare:workers";
import {probe,validateRequest,SOURCES} from "./sources.mjs";
// Private RPC only. No workers.dev, routes, preview URLs or cron. Nothing exposed via HTTP.
export class CerebroTechScoutLab extends WorkerEntrypoint {
  async capability(){return {engine_id:"TECH-SCOUT",version:"0.1.0",environment:"LAB",enabled:this.env.TECHSCOUT_ENABLED==="true",providers:Object.keys(SOURCES),overpass_degraded:true,master_write:false};}
  async probePublic(command,callerToken){return probe(command,callerToken,this.env)}
  async propose(){return {status:"DENIED",reason:"GATEWAY_INBOX_RECONCILIATION_NOT_WIRED"}}
}
export default {async fetch(){return new Response('LAB_PRIVATE_DISABLED',{status:403,headers:{"cache-control":"no-store","content-type":"text/plain"}})}};

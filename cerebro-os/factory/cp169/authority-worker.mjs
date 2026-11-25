import {DurableObject,WorkerEntrypoint} from 'cloudflare:workers';
import {createIndependentAuthority} from './independent-iam.mjs';
import {createBoundedStore,requestId} from './bounded-store.mjs';
const decode=s=>{if(typeof s!=='string'||s.length>200||!/^[A-Za-z0-9+/]+={0,2}$/.test(s))throw Error('KEY_CONFIGURATION_DENIED');return Uint8Array.from(atob(s),c=>c.charCodeAt(0));};
const importPublic=async s=>{const b=decode(s);if(b.length!==32)throw Error('PUBLIC_KEY_LENGTH');return crypto.subtle.importKey('raw',b,{name:'Ed25519'},true,['verify']);};
const importPrivate=s=>crypto.subtle.importKey('pkcs8',decode(s),{name:'Ed25519'},false,['sign']);
export class AuthorityLedger extends DurableObject{
 constructor(ctx,env){super(ctx,env);this.ctx=ctx;this.env=env;}
 async #run(action,c,sig){
  if(this.env.CP168_ENABLED!=='true'||c?.request_id!==requestId)throw Error('CANARY_DISABLED_OR_SCOPE_DENIED');
  const [j,f,a]=await Promise.all([importPublic(this.env.JARVIS_PUBLIC),importPublic(this.env.FACT_PUBLIC),importPrivate(this.env.AUTHORITY_PRIVATE)]);
  const authority=createIndependentAuthority({enabled:true,principalKey:j,readerKey:f,signingKey:a,store:createBoundedStore(this.ctx.storage)});
  return authority[action](c,sig);
 }
 issue(c,s){return this.#run('issue',c,s)}
 current(c,s){return this.#run('current',c,s)}
 revoke(c,s){return this.#run('revoke',c,s)}
}
export class IamAuthorityLab extends WorkerEntrypoint{
 #ledger(c){if(this.env.CP168_ENABLED!=='true'||c?.request_id!==requestId||!this.env.AUTHORITY_LEDGER)throw Error('CANARY_DISABLED_OR_SCOPE_DENIED');const ns=this.env.AUTHORITY_LEDGER.jurisdiction('eu');return ns.get(ns.idFromName('fenix-cp168-bounded-authority'));}
 issue(c,s){return this.#ledger(c).issue(c,s)}
 current(c,s){return this.#ledger(c).current(c,s)}
 revoke(c,s){return this.#ledger(c).revoke(c,s)}
}
export default {async fetch(){return new Response(null,{status:404,headers:{'cache-control':'no-store'}})}};

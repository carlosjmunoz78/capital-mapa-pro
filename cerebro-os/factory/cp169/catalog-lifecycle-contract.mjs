// Additive IAM lifecycle contract for FACT.CATALOG.READ.
// Pure state machine; the existing independent authority must authenticate,
// approve and persist transitions atomically before signing or returning a grant.
// No signing keys, network, live issuer, storage creation or release authority here.
import {catalogGrantScope} from '../../core/minimum/catalog-grant-review.mjs';
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{8,128}$/.test(x);
const ref=x=>typeof x==='string'&&/^[A-Za-z0-9_.:/-]{8,200}$/.test(x);
const exact=(a,b)=>a&&Object.getPrototypeOf(a)===Object.prototype&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([k,v])=>Object.hasOwn(a,k)&&a[k]===v);
const err=x=>{throw Error(x)};
const tick=t=>Number.isSafeInteger(t)&&t>=0;
export function createCatalogLifecycleContract({issuerId,principalId,readerId}={}){
 if(![issuerId,principalId,readerId].every(id)||new Set([issuerId,principalId,readerId]).size!==3)err('ROLE_SCOPE_DENIED');
 const fixed={...catalogGrantScope,issuer_id:issuerId,principal_id:principalId,reader_id:readerId};
 function expected(requestId,receipt,issued,active,revoked){
  return {...fixed,request_id:requestId,policy_receipt_ref:receipt,decision:'ALLOW_READ_ONLY',
    active,revoked,issued_at_epoch:issued,expires_at_epoch:issued+120};
 }
 function validateState(g,requestId,receipt){
  if(!g||!tick(g.issued_at_epoch)||!Number.isSafeInteger(g.issued_at_epoch+120)||
     !(g.active===true&&g.revoked===false||g.active===false&&g.revoked===true)||
     !exact(g,expected(requestId,receipt,g.issued_at_epoch,g.active,g.revoked)))err('PERSISTED_SCOPE_DENIED');
 }
 // This function is not an authentication or authorization boundary.
 // The authority must supply authenticated commands and independently decide
 // permission; a draft state is never itself a valid issued grant.
 function plan({action,requestId,receipt,now,state,readerNonce}={}){
  if(!['issue','current','revoke'].includes(action)||!id(requestId)||!ref(receipt)||!tick(now))err('COMMAND_SCOPE_DENIED');
  if(action==='issue'){
   if(state!==null||!Number.isSafeInteger(now+120))err('GRANT_ALREADY_EXISTS_OR_CLOCK_DENIED');
   return Object.freeze({transition:'INSERT_ONCE',draft:Object.freeze(expected(requestId,receipt,now,true,false)),
     execution_allowed:false,deployment_authorized:false});
  }
  validateState(state,requestId,receipt);
  if(now<state.issued_at_epoch)err('CLOCK_DENIED');
  if(action==='revoke')return Object.freeze({transition:state.revoked?'NOOP_REVOKED':'REVOKE_ATOMIC',
    draft:Object.freeze({...state,active:false,revoked:true}),execution_allowed:false,deployment_authorized:false});
  if(!id(readerNonce)||state.revoked||!state.active||now>=state.expires_at_epoch)err('GRANT_INACTIVE_OR_NONCE_DENIED');
  return Object.freeze({transition:'READ_CURRENT_ONCE',
    draft:Object.freeze({...state,reader_nonce:readerNonce,checked_at_epoch:now}),
    execution_allowed:false,deployment_authorized:false});
 }
 return Object.freeze({plan});
}

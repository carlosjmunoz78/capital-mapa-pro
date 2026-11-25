// Isolated credential lifecycle rehearsal. Never consumes or grants core authority.
const roles=['AUTHORITY','CORE_INGRESS','CORE_MACHINE','CORE_SUPERVISOR','FACT','JARVIS','TRIBUNAL'];
const macs=['FACT_MAC','JARVIS_MAC'];
const enc=new TextEncoder();
const bytes=x=>Uint8Array.from(atob(x),c=>c.charCodeAt(0));
const b64=x=>btoa(String.fromCharCode(...new Uint8Array(x)));
const exact=(a,b)=>JSON.stringify(Object.keys(a??{}).sort())===JSON.stringify([...b].sort());
const message=(role,epoch)=>enc.encode('cerebro.recovery.rehearsal.v1\0'+role+'\0'+epoch);
export async function rehearse(env,id,prior){
 const epoch=env.REISSUE_EPOCH;
 if(env.REISSUE_SCOPE!=='ISOLATED_PREPROD_REHEARSAL'||!['A','B'].includes(epoch)||id!=='core-reissue-rehearsal-20261125-00'+(epoch==='A'?'1':'2'))throw Error('SCOPE_DENIED');
 if(epoch==='A'&&prior!==null||epoch==='B'&&(!exact(prior,['epoch','signatures','macs'])||prior.epoch!=='A'||!exact(prior.signatures,roles)||!exact(prior.macs,macs)))throw Error('PRIOR_DENIED');
 const signatures={},tags={},publicSet=new Set(),macSet=new Set();
 for(const role of roles){
  const pub=env[role+'_PUBLIC'],priv=env[role+'_PRIVATE'];
  if(typeof pub!=='string'||typeof priv!=='string'||bytes(pub).length!==32||publicSet.has(pub))throw Error('KEY_SCOPE');
  publicSet.add(pub);
  const pk=await crypto.subtle.importKey('raw',bytes(pub),'Ed25519',false,['verify']);
  const sk=await crypto.subtle.importKey('pkcs8',bytes(priv),'Ed25519',false,['sign']);
  const sig=await crypto.subtle.sign('Ed25519',sk,message(role,epoch));
  if(!await crypto.subtle.verify('Ed25519',pk,sig,message(role,epoch)))throw Error('PAIR_MISMATCH');
  if(epoch==='B'){
   const old=prior.signatures[role];
   if(!exact(old,['public_key','signature'])||old.public_key===pub)throw Error('ROTATION_DENIED');
   const oldKey=await crypto.subtle.importKey('raw',bytes(old.public_key),'Ed25519',false,['verify']);
   const oldSig=bytes(old.signature);
   if(!await crypto.subtle.verify('Ed25519',oldKey,oldSig,message(role,'A'))||await crypto.subtle.verify('Ed25519',pk,oldSig,message(role,'A')))throw Error('REISSUE_PROOF_DENIED');
  }
  signatures[role]={public_key:pub,signature:b64(sig)};
 }
 for(const role of macs){
  const raw=bytes(env[role]);if(raw.length!==32||macSet.has(env[role]))throw Error('MAC_SCOPE');
  macSet.add(env[role]);
  const k=await crypto.subtle.importKey('raw',raw,{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);
  const tag=await crypto.subtle.sign('HMAC',k,message(role,epoch));
  if(!await crypto.subtle.verify('HMAC',k,tag,message(role,epoch)))throw Error('MAC_PROOF_DENIED');
  if(epoch==='B'&&await crypto.subtle.verify('HMAC',k,bytes(prior.macs[role]),message(role,'A')))throw Error('MAC_ROTATION_DENIED');
  tags[role]=b64(tag);
 }
 return {status:epoch==='A'?'REHEARSAL_INITIAL_IDENTITIES_VERIFIED':'REHEARSAL_REISSUE_VERIFIED',epoch,signatures,macs:tags,ed25519_verified:7,mac_verified:2,old_signatures_rejected:epoch==='B'?7:0,old_macs_rejected:epoch==='B'?2:0,old_signatures_historical_verified:epoch==='B'?7:0,production_authorized:false,dispatch_authorized:false};
}

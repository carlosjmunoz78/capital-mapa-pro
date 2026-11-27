import test from 'node:test';
import assert from 'node:assert/strict';
import {signBody} from '../../factory/cp169/independent-iam.mjs';
import {createCatalogGrantReviewer,catalogGrantScope} from './catalog-grant-review.mjs';
async function fixture(){
 const [a,p,r]=await Promise.all(Array.from({length:3},()=>crypto.subtle.generateKey('Ed25519',true,['sign','verify'])));
 const cfg={issuerId:'fixture:authority',principalId:'fixture:principal',readerId:'fixture:reader',
  authorityPublicKey:a.publicKey,principalPublicKey:p.publicKey,readerPublicKey:r.publicKey,now:()=>100};
 const body={...catalogGrantScope,issuer_id:cfg.issuerId,principal_id:cfg.principalId,
  reader_id:cfg.readerId,request_id:'fixture:request',reader_nonce:'fixture:nonce',
  policy_receipt_ref:'fixture:receipt',decision:'ALLOW_READ_ONLY',active:true,revoked:false,
  issued_at_epoch:90,expires_at_epoch:210,checked_at_epoch:99};
 const review=await createCatalogGrantReviewer(cfg);
 const check=async (changes={},signer=a.privateKey,input={})=>{
  const b={...body,...changes};const envelope={body:b,signature:await signBody(signer,b)};
  return review({envelope,requestId:body.request_id,readerNonce:body.reader_nonce,
   policyReceiptRef:body.policy_receipt_ref,...input});
 };
 return {a,p,r,cfg,body,check,review};
}
test('exact signed production scope is review only',async()=>{
 const f=await fixture(),r=await f.check();
 assert.equal(r.status,'GRANT_EVIDENCE_VERIFIED');assert.equal(r.execution_allowed,false);
 assert.equal(r.deployment_authorized,false);
});
test('legacy inventory and PREPROD or LAB grants denied',async()=>{
 const f=await fixture();
 for(const x of [{capability:'FACT.INVENTORY.READ'},{environment:'PREPROD'},{environment:'LAB'}])
  assert.equal((await f.check(x)).status,'BLOCKED');
});
test('no mutation, extra cost, other tenant or version',async()=>{
 const f=await fixture();
 for(const x of [{external_mutation_allowed:true},{read_only:false},{cost_ceiling_eur:1},{company_id:'other'},{version:'1.1.0'}])
  assert.equal((await f.check(x)).status,'BLOCKED');
});
test('revoked, inactive and wrong principal, reader or issuer rejected',async()=>{
 const f=await fixture();
 for(const x of [{revoked:true},{active:false},{principal_id:'fixture:other'},{reader_id:'fixture:other'},{issuer_id:'fixture:other'}])
  assert.equal((await f.check(x)).status,'BLOCKED');
});
test('wrong request, nonce or receipt rejected',async()=>{
 const f=await fixture();
 for(const x of [{request_id:'fixture:other'},{reader_nonce:'fixture:other'},{policy_receipt_ref:'fixture:other'}])
  assert.equal((await f.check(x)).status,'BLOCKED');
});
test('expired, stale, future and excessive lifetime denied',async()=>{
 const f=await fixture();
 for(const x of [{issued_at_epoch:0,expires_at_epoch:100},{checked_at_epoch:89},{checked_at_epoch:101},{expires_at_epoch:211}])
  assert.equal((await f.check(x)).status,'BLOCKED');
});
test('wrong signer and additional privilege rejected',async()=>{
 const f=await fixture();
 assert.equal((await f.check({},f.p.privateKey)).status,'BLOCKED');
 assert.equal((await f.check({admin:true})).status,'BLOCKED');
});
test('key reuse rejected',async()=>{
 const f=await fixture();
 await assert.rejects(createCatalogGrantReviewer({...f.cfg,readerPublicKey:f.a.publicKey}),/KEY_SEPARATION_DENIED/);
});
test('no grant provided',async()=>{
 const f=await fixture();
 assert.equal((await f.review()).status,'BLOCKED');
});

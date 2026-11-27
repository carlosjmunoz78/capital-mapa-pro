import test from 'node:test';
import assert from 'node:assert/strict';
import {createCatalogLifecycleContract} from './catalog-lifecycle-contract.mjs';
import {createCatalogGrantReviewer} from '../../core/minimum/catalog-grant-review.mjs';
import {signBody} from './independent-iam.mjs';
const roles={issuerId:'fixture:authority',principalId:'fixture:principal',readerId:'fixture:reader'};
const lifecycle=createCatalogLifecycleContract(roles);
const base={requestId:'fixture:request',receipt:'fixture:receipt',now:90};
const plan=(action,changes={})=>lifecycle.plan({action,...base,state:null,...changes});
const issued=()=>plan('issue').draft;
test('issue draft exact production capability and bounded expiry',()=>{
 const p=plan('issue');
 assert.equal(p.transition,'INSERT_ONCE');assert.equal(p.draft.capability,'FACT.CATALOG.READ');
 assert.equal(p.draft.environment,'PROD');assert.equal(p.draft.expires_at_epoch,210);
 assert.equal(p.draft.read_only,true);assert.equal(p.draft.external_mutation_allowed,false);
 assert.equal(p.draft.cost_ceiling_eur,0);assert.equal(p.execution_allowed,false);
});
test('new lifecycle matches existing signature reviewer in fixture only',async()=>{
 const [a,p,r]=await Promise.all(Array.from({length:3},()=>crypto.subtle.generateKey('Ed25519',true,['sign','verify'])));
 const review=await createCatalogGrantReviewer({...roles,authorityPublicKey:a.publicKey,
 principalPublicKey:p.publicKey,readerPublicKey:r.publicKey,now:()=>100});
 const d=plan('current',{state:issued(),now:100,readerNonce:'fixture:nonce'}).draft;
 const out=await review({envelope:{body:d,signature:await signBody(a.privateKey,d)},requestId:base.requestId,
 readerNonce:'fixture:nonce',policyReceiptRef:base.receipt});
 assert.equal(out.status,'GRANT_EVIDENCE_VERIFIED');assert.equal(out.execution_allowed,false);
});
test('cannot issue duplicate or replace revoked grant',()=>{
 assert.throws(()=>plan('issue',{state:issued()}),/GRANT_ALREADY_EXISTS/);
 assert.throws(()=>plan('issue',{state:plan('revoke',{state:issued()}).draft}),/GRANT_ALREADY_EXISTS/);
});
test('revocation is terminal and idempotent',()=>{
 const revoked=plan('revoke',{state:issued(),now:100});
 assert.equal(revoked.transition,'REVOKE_ATOMIC');assert.equal(revoked.draft.active,false);
 assert.equal(revoked.draft.revoked,true);
 assert.equal(plan('revoke',{state:revoked.draft,now:101}).transition,'NOOP_REVOKED');
 assert.throws(()=>plan('current',{state:revoked.draft,now:101,readerNonce:'fixture:nonce'}),/GRANT_INACTIVE/);
});
test('expiry, backward clock and nonce required',()=>{
 assert.throws(()=>plan('current',{state:issued(),now:210,readerNonce:'fixture:nonce'}),/GRANT_INACTIVE/);
 assert.throws(()=>plan('current',{state:issued(),now:89,readerNonce:'fixture:nonce'}),/CLOCK_DENIED/);
 assert.throws(()=>plan('current',{state:issued(),now:100}),/GRANT_INACTIVE/);
});
test('legacy permission, tenant, escalation and mismatched requests denied',()=>{
 for(const changed of [{capability:'FACT.INVENTORY.READ'},{environment:'LAB'},{environment:'PREPROD'},
 {company_id:'other'},{external_mutation_allowed:true},{cost_ceiling_eur:1},{request_id:'fixture:other'},
 {policy_receipt_ref:'fixture:other'},{admin:true}])
 assert.throws(()=>plan('current',{state:{...issued(),...changed},readerNonce:'fixture:nonce'}),/PERSISTED_SCOPE_DENIED/);
});
test('role separation and no unknown commands',()=>{
 assert.throws(()=>createCatalogLifecycleContract({...roles,readerId:roles.issuerId}),/ROLE_SCOPE_DENIED/);
 assert.throws(()=>plan('write'),/COMMAND_SCOPE_DENIED/);
});

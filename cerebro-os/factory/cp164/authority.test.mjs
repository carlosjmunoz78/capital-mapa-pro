import {test} from 'node:test';import assert from 'node:assert/strict';import {request,control,sign,verify,exact,makeGrant,current,revoked,now} from './authority.mjs';
const k='a'.repeat(64),t=now();
test('signed exact request',async()=>{const r=request(t);assert(exact(r,request(t),t));assert(await verify(k,r,await sign(k,r)));});
test('signature tamper',async()=>{const r=request(t);assert.equal(await verify(k,{...r,company_id:'fenix-capital'},await sign(k,r)),false);assert.equal(await verify(k,r,'0'.repeat(64)),false);});
test('deny scope and extra claims',()=>{for(const r of [{...request(t),company_id:'fenix-capital'},{...request(t),environment:'PROD'},{...request(t),verified:true}])assert.throws(()=>makeGrant(r,t),/SCOPE_DENIED/);});
test('deny stale or future',()=>{for(const n of [t-61,t+1])assert.throws(()=>makeGrant(request(n),t),/SCOPE_DENIED/);});
test('grant live, expires, revoke',()=>{const g=makeGrant(request(t),t);assert.equal(current(g,t+1).checked_at_epoch,t+1);assert.throws(()=>current(g,t+120),/INACTIVE/);assert.throws(()=>current(revoked(g,t+1),t+1),/INACTIVE/);});
test('control domain separation',async()=>{assert.equal(await verify(k,control('revoke',t),await sign(k,control('inspect',t))),false);});

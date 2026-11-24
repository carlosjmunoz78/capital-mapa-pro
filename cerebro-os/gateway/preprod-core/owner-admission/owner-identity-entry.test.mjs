import {test} from 'node:test';import assert from 'node:assert/strict';import worker from './owner-identity-entry.mjs';
const env={CORE_ENV:'PREPROD',OWNER_PROBE_ENABLED:'true',ACCESS_ISSUER:'https://fixture.cloudflareaccess.com',ACCESS_AUD:'preprod-test',ACCESS_LAB_AUD:'lab-test',ACCESS_OWNER_EMAIL:'owner@example.invalid',ACCESS_OWNER_SUB:'owner-test-sub',ACCESS_ORIGIN:'https://preprod.example.invalid'};
const pair=await crypto.subtle.generateKey({name:'RSASSA-PKCS1-v1_5',modulusLength:2048,publicExponent:new Uint8Array([1,0,1]),hash:'SHA-256'},true,['sign','verify']);
const jwk={...await crypto.subtle.exportKey('jwk',pair.publicKey),kid:'fixture',alg:'RS256',use:'sig'};
globalThis.fetch=async()=>new Response(JSON.stringify({keys:[jwk]}));
const b64=x=>Buffer.from(JSON.stringify(x)).toString('base64url');
async function token(overrides={}){const t=Math.floor(Date.now()/1000),s=b64({alg:'RS256',kid:'fixture'})+'.'+b64({iss:env.ACCESS_ISSUER,aud:[env.ACCESS_AUD],email:env.ACCESS_OWNER_EMAIL,sub:env.ACCESS_OWNER_SUB,type:'app',iat:t,exp:t+900,...overrides});return s+'.'+Buffer.from(await crypto.subtle.sign('RSASSA-PKCS1-v1_5',pair.privateKey,Buffer.from(s))).toString('base64url');}
const req=(t,path='/identity',method='GET')=>new Request(env.ACCESS_ORIGIN+path,{method,headers:t?{'Cf-Access-Jwt-Assertion':t}:{}});
test('valid app identity no grant or dispatch',async()=>{const r=await worker.fetch(req(await token()),env),j=await r.json();assert.equal(r.status,200);assert.equal(j.status,'OWNER_IDENTITY_PREPROD_VERIFIED');assert.equal(j.dispatch_authorized,false);assert.equal(j.promotion_allowed,false);assert.equal(j.subject_sha256.length,64);assert.ok(!('email'in j));});
test('no JWT',async()=>assert.equal((await worker.fetch(req(),env)).status,403));
test('wrong audience or user',async()=>{for(const claims of [{aud:[env.ACCESS_LAB_AUD]},{sub:'other'},{email:'other@example.invalid'},{type:'org'}])assert.equal((await worker.fetch(req(await token(claims)),env)).status,403);});
test('closed paths, query, writes and disabled runtime',async()=>{const t=await token();for(const q of [req(t,'/'),req(t,'/identity?x=1'),req(t,'/identity','POST')])assert.equal((await worker.fetch(q,env)).status,404);assert.equal((await worker.fetch(req(t),{...env,OWNER_PROBE_ENABLED:'false'})).status,404);});

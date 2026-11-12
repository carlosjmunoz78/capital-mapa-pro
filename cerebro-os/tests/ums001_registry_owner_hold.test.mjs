import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const data=JSON.parse(readFileSync(new URL('../registry/ums001_multi_runtime_connection_matrix.lab.json',import.meta.url),'utf8'));
test('WordPress STAGING stays suspended until a new owner order',()=>{
  assert.equal(data.owner_directive?.wordpress_staging,'SUSPENDED_UNTIL_OWNER_NEW_ORDER');
  const staging=data.routing.find(x=>x.runtime==='SEO_WORDPRESS_STAGING');
  assert.equal(staging?.state,'SUSPENDED_BY_OWNER_UNTIL_NEW_ORDER');
  assert.equal(staging?.skip_monitoring,true);
});
test('Social universal IAM must not be claimed live without actual E2E',()=>{
  const soc=data.routing.find(x=>x.runtime==='SOCIAL_CLOUDFLARE_UNIVERSAL_NEW');
  assert.ok(soc);
  if(!soc.e2e_verified){
    assert.ok(!['HECHO_VERIFICADO','ACTIVE_PROD'].includes(soc.state));
    assert.ok(soc.flags.includes('SOCIAL_UNIVERSAL_IAM_ENABLED=false'));
  }
});

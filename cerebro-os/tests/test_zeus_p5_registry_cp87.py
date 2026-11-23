import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NODE=shutil.which('node')
MOD=ROOT/'supervisor'/'cloudflare'/'zeus_p5_registry_router_cp87.mjs'

class ZeusP5RegistryCP87(unittest.TestCase):
    @unittest.skipUnless(NODE,'Node interpreter needed')
    def test_registry_and_incident_deduplication(self):
        script=r"""
import {normalizeZeusP5Receipt,ingestZeusP5Supervisor} from './supervisor/cloudflare/zeus_p5_registry_router_cp87.mjs';
import assert from 'node:assert/strict';
const day='20261123',now=Date.parse('2026-11-23T09:50:00Z');
const good={receipt_id:'ZEUS-P5-'+day+'-fenix-capital-LAB',company_id:'fenix-capital',engine_id:'FACT-001',environment:'LAB',version:'1.0.0',day_key:day,request_id:'FACT001-P5-'+day,state:'GREEN',code:'GREEN',observed_at_ms:now,fingerprint_sha256:'a'.repeat(64),source:'ZEUS_P5_SHARED_RUNTIME'};
assert.equal(normalizeZeusP5Receipt(good,day).registry_state,'LAB_GREEN');
for(const change of [{company_id:'aion'},{environment:'PROD'},{code:'NOT_REAL'},{source:'FAKE'},{fingerprint_sha256:'not-hex'}]){
 assert.throws(()=>normalizeZeusP5Receipt({...good,...change},day),/UNTRUSTED/);
}
const reg=new Map(),inc=new Map();let registryWrites=0,incidentWrites=0,sourceReads=0;
const db={prepare(sql){return{bind(...args){return {
 async first(){
 if(sql.includes('FROM zeus_fact_p5_health_v1')){sourceReads++;return db.source;}
 if(sql.includes('FROM zeus_fact_p5_registry_projection_v1'))return reg.get(args[0])||null;
 if(sql.includes('FROM zeus_fact_p5_exceptions_v1'))return inc.get(args[0])||null;
 throw Error('unknown select '+sql);},
 async run(){
 if(sql.startsWith('INSERT INTO zeus_fact_p5_registry_projection_v1')){
 registryWrites++;if(!reg.has(args[0]))reg.set(args[0],{registry_state:args[8],health_code:args[9],receipt_id:args[6],source_sha256:args[11],promotion_allowed:0});
 }else if(sql.startsWith('INSERT INTO zeus_fact_p5_exceptions_v1')){
 incidentWrites++;if(!inc.has(args[0]))inc.set(args[0],{code:args[7],exception_class:args[8],human_required:args[9],source_sha256:args[10],incident_state:'OPEN'});
 }else throw Error('unexpected write '+sql);
 return {};
 }};}}}};
const env={RECOVERY_DB:db,ZEUS_P5_ROUTER_ENABLED:'true'};
assert.equal((await ingestZeusP5Supervisor({RECOVERY_DB:db},now)).status,'OFF');
assert.equal((await ingestZeusP5Supervisor(env,Date.parse('2026-11-23T01:00:00Z'))).status,'NOT_DUE');
db.source=null;
assert.equal((await ingestZeusP5Supervisor(env,now)).status,'AWAIT_SOURCE');
db.source=good;
const one=await ingestZeusP5Supervisor(env,now);
assert.equal(one.registry_state,'LAB_GREEN');
assert.equal(one.incident_id,null);
const twice=await ingestZeusP5Supervisor(env,now+300000);
assert.equal(twice.registry_state,'LAB_GREEN');assert.equal(reg.size,1);assert.equal(inc.size,0);
assert.equal(sourceReads,3);
const blocked={...good,code:'NEW_RECONCILE',state:'BLOCKED',fingerprint_sha256:'b'.repeat(64)};
db.source=blocked;reg.clear();inc.clear();registryWrites=0;incidentWrites=0;
const fail=await ingestZeusP5Supervisor(env,now);
assert.equal(fail.registry_state,'BLOCKED');
assert.equal(fail.human_required,true);
assert.equal(inc.get(fail.incident_id)?.exception_class,'LOW_CONFIDENCE');
await ingestZeusP5Supervisor(env,now+300000);
assert.equal(inc.size,1);assert.equal(reg.size,1);
assert.equal(inc.get(fail.incident_id)?.human_required,1);
db.source={...good,company_id:'evil'};
await assert.rejects(ingestZeusP5Supervisor(env,now),/UNTRUSTED/);
console.log(JSON.stringify({status:'PASS',assertions:18}));
"""
        r=subprocess.run([NODE,'--input-type=module','-e',script],cwd=ROOT,text=True,capture_output=True,timeout=35)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout.splitlines()[-1])['status'],'PASS')

    def test_static_fail_closed_no_new_transport(self):
        s=MOD.read_text(encoding='utf-8')
        self.assertNotIn('fetch(',s)
        self.assertNotIn('DELETE FROM',s)
        self.assertNotIn('UPDATE fact001',s)
        self.assertIn("ZEUS_P5_ROUTER_ENABLED",s)
        self.assertIn('ON CONFLICT(snapshot_id) DO NOTHING',s)
        self.assertIn('ON CONFLICT(incident_id) DO NOTHING',s)
        self.assertIn('promotion_allowed:false',s)
        self.assertNotIn('sendEmail',s)
        self.assertNotIn('return new Response(',s)
        wrapper=(ROOT/'supervisor'/'cloudflare'/'recovery-wrapper-zeus-cp87.mjs').read_text(encoding='utf-8')
        self.assertIn('recovery.scheduled(controller,env,ctx);',wrapper)
        self.assertIn('scheduledP5(env,controller.scheduledTime)',wrapper)
        self.assertIn('superviseP5Daily(env,controller.scheduledTime)',wrapper)
        self.assertIn('ingestZeusP5Supervisor(env,controller.scheduledTime)',wrapper)

if __name__=='__main__': unittest.main()

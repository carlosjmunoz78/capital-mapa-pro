import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"supervisor"/"cloudflare"/"zeus_fact_p5_monitor_v1.mjs"
NODE=shutil.which("node")
class ZeusP5SharedRuntimeCP86(unittest.TestCase):
    @unittest.skipUnless(NODE,"Node interpreter needed")
    def test_deterministic_scope_and_journal_replay(self):
        script=r"""
import {evaluateP5Health,superviseP5Daily} from './supervisor/cloudflare/zeus_fact_p5_monitor_v1.mjs';
import assert from 'node:assert/strict';
const day='20261123', at=Date.parse('2026-11-23T10:30:00Z');
const registry={company_id:'fenix-capital',engine_id:'FACT-001',environment:'LAB',version:'1.0.0',enabled:1,max_daily_jobs:1};
const job={request_id:'FACT001-P5-'+day,company_id:'fenix-capital',engine_id:'FACT-001',environment:'LAB',version:'1.0.0',state:'COMPLETED',attempts:1,max_cost_eur:0,result_valid:1};
assert.equal(evaluateP5Health({registry,job,dayKey:day}).state,'GREEN');
assert.equal(evaluateP5Health({registry,job:null,dayKey:day}).code,'DAILY_JOB_MISSING_OR_SCOPE_INVALID');
assert.equal(evaluateP5Health({registry,job:{...job,state:'RECONCILE'},dayKey:day}).state,'BLOCKED');
assert.equal(evaluateP5Health({registry,job,newReconcileCount:1,dayKey:day}).code,'NEW_RECONCILE');
assert.equal(evaluateP5Health({registry:{...registry,enabled:0},job,dayKey:day}).code,'AUTOMATION_DRIFT');
assert.equal(evaluateP5Health({registry,job:{...job,max_cost_eur:1},dayKey:day}).code,'RECEIPT_OR_COST_INVALID');
let records=new Map(),writes=0,jobReads=0;
const db={prepare(sql){return{bind(...args){return{
 async first(){if(sql.startsWith('SELECT receipt_id,state')) return records.get(args[0])||null;
 if(sql.includes('FROM fact001_p5_automation_registry_v1')) return registry;
 if(sql.includes('FROM fact001_p5_jobs_v1 WHERE request_id')){jobReads++;return job;}
 if(sql.includes('COUNT(*) AS n')) return {n:0};
 throw Error('unexpected SELECT '+sql);},
 async run(){if(!sql.startsWith('INSERT INTO zeus_fact_p5_health_v1'))throw Error('unauthorized write');
 writes++;const id=args[0];if(!records.has(id))records.set(id,{receipt_id:id,state:args[7],code:args[8],fingerprint_sha256:args[10]});
 return {};}};}};}};
const off=await superviseP5Daily({RECOVERY_DB:db},at);assert.equal(off.status,'OFF');
const early=await superviseP5Daily({RECOVERY_DB:db,ZEUS_P5_MONITOR_ENABLED:'true'},Date.parse('2026-11-23T01:00:00Z'));assert.equal(early.status,'NOT_DUE');
const first=await superviseP5Daily({RECOVERY_DB:db,ZEUS_P5_MONITOR_ENABLED:'true'},at);
assert.equal(first.status,'RECORDED');assert.equal(first.state,'GREEN');
const second=await superviseP5Daily({RECOVERY_DB:db,ZEUS_P5_MONITOR_ENABLED:'true'},at+300000);
assert.equal(second.status,'ALREADY_RECORDED');assert.equal(writes,1);assert.equal(jobReads,1);
assert.equal(records.size,1);
console.log(JSON.stringify({status:'PASS',tests:10,stored:records.size,writes,jobReads}));
"""
        run=subprocess.run([NODE,"--input-type=module","-e",script],cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr)
        report=json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(report["status"],"PASS")
        self.assertEqual(report["stored"],1)

    def test_isolation_and_no_new_cron_or_external_mutation(self):
        s=MODULE.read_text(encoding="utf-8")
        self.assertNotIn("fetch(",s)
        self.assertNotIn("retry",s.lower())
        self.assertNotIn("DELETE FROM",s)
        self.assertNotIn("UPDATE fact001_p5_jobs_v1",s)
        self.assertIn("ZEUS_P5_MONITOR_ENABLED",s)
        self.assertIn("ON CONFLICT(receipt_id) DO NOTHING",s)
        wrapper=(ROOT/"supervisor"/"cloudflare"/"recovery-wrapper-zeus-cp86.mjs").read_text(encoding="utf-8")
        self.assertNotIn("crons",wrapper)
        self.assertIn("recovery.scheduled(controller,env,ctx);",wrapper)
        self.assertIn("scheduledP5(env,controller.scheduledTime)",wrapper)
        self.assertIn("superviseP5Daily(env,controller.scheduledTime)",wrapper)
if __name__=="__main__":unittest.main()

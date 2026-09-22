import importlib.util
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import zipfile
import hashlib

ROOT=pathlib.Path(__file__).resolve().parents[1]
EXT=ROOT/"identity"/"chrome_extension_v1_6_1"
WORKER=EXT/"service_worker.js"
INSTALLER=ROOT/"identity"/"windows"/"recovery_v1_6_1"/"Install-CerebroBrowserReplayGuardV161.ps1"
SERVICE=ROOT/"identity"/"windows"/"CerebroBrowserBridgeService.ps1"

class ReplayGuardV161Tests(unittest.TestCase):
 def test_parallel_installation_preserves_v160(self):
  old=json.loads((ROOT/"identity"/"chrome_extension_v1_6"/"manifest.json").read_text())
  new=json.loads((EXT/"manifest.json").read_text())
  self.assertEqual(old["version"],"1.6.0")
  self.assertEqual(new["version"],"1.6.1")
  self.assertEqual(set(new["permissions"])-set(old["permissions"]),{"storage"})
  self.assertEqual(old["host_permissions"],new["host_permissions"])
  self.assertNotIn("<all_urls>",new["host_permissions"])
  source=SERVICE.read_text(encoding="utf-8")
  self.assertIn('("1.4.1","1.5.0","1.6.0","1.6.1")',source)
  self.assertIn('("1.6.0","1.6.1")',source)
  inst=INSTALLER.read_text()
  for required in ('PAYLOAD_HASH_MISMATCH','SNAPSHOT','ROLLED_BACK','REQUIRES_INSTALLED_V160','prod_disabled','PREVIOUS_PATCH_PENDING_ACCEPTANCE'):
   self.assertIn(required,inst)
  self.assertIn('for($attempt=1;$attempt -le 30;$attempt++)',inst)
  self.assertIn('LOCAL_BRIDGE_VERIFY_TIMEOUT',inst)
  self.assertIn('$candidate.checks.service_found',inst)
  self.assertIn('$candidate.checks.paired',inst)
  for forbidden in ('Stop-Process -Name chrome','Remove-Item -Recurse','<all_urls>'):
   self.assertNotIn(forbidden,inst)
 def test_zip_integrity_and_previous_artifacts_untouched(self):
  spec=importlib.util.spec_from_file_location("replay_guard_builder",ROOT/"jobs"/"build_browser_replay_guard_v161.py")
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/"patch.zip"
   meta=module.build(out)
   self.assertFalse(meta["prod_enabled"]);self.assertFalse(meta["credentials_included"])
   with zipfile.ZipFile(out) as z:
    hashes=json.loads(z.read("payload-sha256.json"))
    self.assertEqual(set(hashes),set(module.PAYLOAD))
    for name,sha in hashes.items():
     self.assertEqual(hashlib.sha256(z.read("payload/"+name)).hexdigest(),sha)
    self.assertEqual(json.loads(z.read("payload/chrome_extension_v1_4_1/manifest.json"))["version"],"1.6.1")
    self.assertIn("ROLLBACK.bat",z.namelist())
 @unittest.skipUnless(shutil.which("node"),"Node required")
 def test_no_duplicate_tabs_when_receipt_unavailable(self):
  script=r"""
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const worker=fs.readFileSync(process.argv[1],"utf8");
const saved={},opened=[];
let alarm,receipts=0;
const chrome={
 runtime:{id:"a".repeat(32),onInstalled:{addListener(){}},onStartup:{addListener(){}}},
 alarms:{onAlarm:{addListener(f){alarm=f}},create(){}},
 storage:{local:{
  async get(k){return {[k]:saved[k]}},
  async set(obj){Object.assign(saved,obj)}
 }},
 tabs:{async query(){return opened.slice()},async create({url}){const tab={id:opened.length+1,url,status:"complete"};opened.push(tab);return tab}}
};
const command={decision:"LAB_COMMAND_AVAILABLE",environment:"LAB",
 company_id:"fenix",external_mutation_allowed:false,action:"OPEN_LOCAL_TEST_PAGE",
 command_id:"local-161-a",target_url:"http://127.0.0.1:8765/lab/test?command_id=local-161-a"};
async function fetcher(input){
 const u=new URL(input);
 let status=200,body={};
 if(u.pathname==="/extension/ping") {
  assert.equal(u.searchParams.get("extension_version"),"1.6.1");
  body={status:"GREEN",service_version:"1.4.1"};
 } else if(u.pathname==="/extension/command"){body=command}
 else if(u.pathname==="/extension/result"){
  receipts++;
  if(receipts===1){status=400;body={status:"BLOCKED",decision:"TEMPORARILY_UNAVAILABLE"}}
  else body={status:"GREEN",decision:"LAB_COMMAND_RECEIPT_ACCEPTED"};
 } else {throw new Error("Unexpected endpoint: "+u.pathname)}
 return {ok:status===200,async json(){return body}};
}
const warnings=[];
vm.runInNewContext(worker,{chrome,fetch:fetcher,URL,encodeURIComponent,
 console:{warn(...args){warnings.push(args)}},setTimeout});
(async()=>{
 await new Promise(resolve=>setTimeout(resolve,50));
 assert.equal(typeof alarm,"function");
 for(let i=0;i<3;i++)await alarm({name:"cerebro-heartbeat"});
 assert.equal(opened.length,1,"unacknowledged replay opened another tab");
 assert.equal(receipts,4);
 assert.equal(saved.cerebro_local_test_receipt_v161.command_id,command.command_id);
 assert.equal(saved.cerebro_local_test_receipt_v161.success,true);
 assert.equal(warnings[0][0],"CEREBRO_LOCAL_RECEIPT_UNCONFIRMED");
})().catch(e=>{console.error(e);process.exitCode=1});
"""
  proc=subprocess.run(["node","-e",script,str(WORKER)],capture_output=True,text=True,timeout=20)
  self.assertEqual(proc.returncode,0,proc.stderr+proc.stdout)
if __name__=="__main__":unittest.main()

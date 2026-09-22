import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
BUILDER=ROOT/"jobs"/"build_browser_replay_guard_v162.py"
INSTALL=ROOT/"identity"/"windows"/"recovery_v1_6_2"/"Install-CerebroBrowserReplayGuardV162.ps1"
SERVICE=ROOT/"identity"/"windows"/"CerebroBrowserBridgeService.ps1"
EXT=ROOT/"identity"/"chrome_extension_v1_6_2"

class V162PackageTests(unittest.TestCase):
 def test_scoped_parallel_upgrade(self):
  new=json.loads((EXT/"manifest.json").read_text(encoding="utf-8"))
  old=json.loads((ROOT/"identity"/"chrome_extension_v1_6_1"/"manifest.json").read_text(encoding="utf-8"))
  self.assertEqual(new["version"],"1.6.2")
  self.assertEqual(old["version"],"1.6.1")
  self.assertEqual(new["host_permissions"],old["host_permissions"])
  self.assertEqual(new["permissions"],old["permissions"])
  self.assertNotIn("<all_urls>",new["host_permissions"])
  installer=INSTALL.read_text(encoding="utf-8")
  service=SERVICE.read_text(encoding="utf-8")
  for text in ['if($current.version -ne "1.6.1")','REQUIRES_INSTALLED_V161',
    'recovery-v1.6.1.json',
    'recovery-v1.6.2.json','recovery-backup-v162','"1.6.2"',
    'LOCAL_BRIDGE_VERIFY_TIMEOUT','Restore $Report.target $Report.backup',
    'payload-sha256.json','[bool]$candidate.kill_switch_enabled']:
   self.assertIn(text,installer)
  self.assertIn('("1.4.1","1.5.0","1.6.0","1.6.1","1.6.2")',service)
  self.assertIn('@("1.6.0","1.6.1","1.6.2")',service)
  self.assertNotIn('Stop-Process -Name chrome',installer)
  self.assertNotIn('Remove-Item -Recurse',installer)
 def test_zip_integrity_and_rollback_files(self):
  spec=importlib.util.spec_from_file_location("v162build",BUILDER)
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as td:
   out=pathlib.Path(td)/"v162.zip"
   meta=module.build(out)
   self.assertEqual(meta["package_version"],"1.6.2")
   self.assertFalse(meta["prod_enabled"])
   self.assertFalse(meta["external_mutation_allowed"])
   self.assertFalse(meta["credentials_included"])
   self.assertEqual(hashlib.sha256(out.read_bytes()).hexdigest(),meta["sha256"])
   with zipfile.ZipFile(out) as z:
    sha=json.loads(z.read("payload-sha256.json"))
    self.assertEqual(set(sha),set(module.PAYLOAD))
    for name,digest in sha.items():
     self.assertEqual(hashlib.sha256(z.read("payload/"+name)).hexdigest(),digest)
    self.assertEqual(json.loads(z.read("payload/chrome_extension_v1_4_1/manifest.json"))["version"],"1.6.2")
    self.assertIn("ROLLBACK.bat",z.namelist())
    self.assertIn("INSTALL_AND_VERIFY.bat",z.namelist())
    self.assertIn("README.txt",z.namelist())

if __name__=="__main__": unittest.main()

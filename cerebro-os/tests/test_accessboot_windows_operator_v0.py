"""ACCESSBOOT Windows operator V0 contract tests."""
import json, pathlib, re, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
PKG=ROOT/"identity"/"windows"/"accessboot_v0"
class T(unittest.TestCase):
 def test_manifest(self):
  m=json.loads((PKG/"payload/chrome_extension_v1_4_1/manifest.json").read_text())
  self.assertEqual(m["version"],"1.7.0"); self.assertIn("tabs",m["permissions"]); self.assertIn("https://*/*",m["host_permissions"])
 def test_filesystem_is_bounded(self):
  s=(PKG/"payload/CerebroBrowserTransport.ps1").read_text()
  for x in ('FS_CREATE_DIRECTORY','GetFolderPath("MyDocuments")','FS_PATH_DENIED','FS_SCOPE_DENIED','DIRECTORY_EXISTS_VERIFIED'): self.assertIn(x,s)
  self.assertNotIn('Invoke-Expression',s); self.assertNotIn('cmd.exe /c',s)
 def test_browser_is_https_policy(self):
  b=(PKG/"payload/CerebroBrowserBridgeService.ps1").read_text()
  w=(PKG/"payload/chrome_extension_v1_4_1/service_worker.js").read_text()
  for x in ('BROWSER_OPEN_URL','BROWSER_URL_SCOPE_DENIED','https','localhost','192\\.168'): self.assertIn(x,b)
  for x in ('BROWSER_OPEN_URL','BROWSER_URL_OPENED_VERIFIED','chrome.tabs.create','u.protocol!=="https:"'): self.assertIn(x,w)
 def test_prod_not_enabled(self):
  i=(PKG/"Install-CerebroAccessbootV0.ps1").read_text()
  self.assertIn('prod_enabled=$false',i); self.assertIn('environment -eq "LAB"',i); self.assertIn('kill_switch_enabled',i)
if __name__=="__main__": unittest.main()

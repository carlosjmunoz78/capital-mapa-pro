import json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
EXT=ROOT/"identity"/"chrome_extension_v1_6"
class BrowserOperatorV16Tests(unittest.TestCase):
 def test_permissions_are_local_fixture_only(self):
  m=json.loads((EXT/"manifest.json").read_text())
  self.assertEqual(m["version"],"1.6.0");self.assertEqual(m["host_permissions"],["http://127.0.0.1/*","https://example.com/*"])
  self.assertIn("scripting",m["permissions"]);self.assertNotIn("tabs",m["permissions"])
 def test_executor_is_deterministic_and_no_arbitrary_origin(self):
  s=(EXT/"service_worker.js").read_text()
  for a in ("OPERATOR_CLICK","OPERATOR_TYPE","OPERATOR_SELECT","OPERATOR_READ"):self.assertIn(a,s)
  for selector in ("#cerebro-button","#cerebro-input","#cerebro-select","#cerebro-output"):self.assertIn(selector,s)
  self.assertIn('c.target_url==="http://127.0.0.1:"',s)
  self.assertNotIn("chrome.cookies",s);self.assertIn('ALLOWED_URL = "https://example.com/"',s)
  self.assertIn("value.length>64",s);self.assertIn("SELECTOR_DENIED",s)
 def test_fixture_has_only_expected_controls(self):
  h=(ROOT/"identity"/"browser_operator_fixture_v16.html").read_text()
  for selector in ('id="cerebro-input"','id="cerebro-select"','id="cerebro-button"','id="cerebro-output"'):self.assertIn(selector,h)
if __name__=="__main__":unittest.main()

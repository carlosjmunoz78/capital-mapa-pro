import unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"registry/NEWS001_BREVO_AUTOMATION_ALIGNMENT_20261118.json"
class TestNews001AutomationAlignment(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.x=json.loads(FILE.read_text(encoding="utf-8"))
 def test_all_7_existing_flows_preserved(self):
  self.assertEqual({f["id"] for f in self.x["legacy_flows"]},{1,2,4,5,7,8,9})
  self.assertEqual(sum(f["state"]=="active" for f in self.x["legacy_flows"]),6)
  self.assertEqual(sum(f["state"]=="inactive" for f in self.x["legacy_flows"]),1)
 def test_exact_list_snapshot(self):
  d={x["list_id"]:x["unique_subscribers"] for x in self.x["legacy_list_snapshot"]}
  self.assertEqual(d[10],23);self.assertEqual(d[15],11)
  self.assertEqual(d[17],0);self.assertEqual(d[18],0)
 def test_news001_never_uses_old_list_for_target(self):
  x=self.x["new_newsletters"]["audiences"]
  self.assertEqual(x["particulares"]["brevo_list_id"],17)
  self.assertEqual(x["inmobiliarias"]["brevo_list_id"],18)
  old={f["trigger"]["list_id"] for f in self.x["legacy_flows"]}
  self.assertFalse({17,18}&old)
  self.assertFalse({17,18}&set(x["particulares"]["never_import_legacy"]))
 def test_old_particulares_not_reused(self):
  x=self.x
  self.assertEqual(next(f["trigger"]["list_id"] for f in x["legacy_flows"] if f["id"]==9),10)
  self.assertEqual(next(f["role"] for f in x["legacy_flows"] if f["id"]==9),"LEGACY_NEWSLETTER_B2C")
  self.assertIn(10,x["new_newsletters"]["audiences"]["particulares"]["never_import_legacy"])
 def test_salinas_blocked(self):
  self.assertEqual(self.x["new_newsletters"]["audiences"]["inmobiliarias"]["exclude_business"],"Salinas")
 def test_no_claims_of_live_migration(self):
  p=self.x["non_mutation"]
  for key,value in p.items():self.assertIs(value,False,(key,value))
  self.assertIsNone(self.x["new_newsletters"]["activation_at"])
  self.assertIs(self.x["new_newsletters"]["prod_enabled"],False)
 def test_no_style_regression(self):
  x=self.x["homogeneous_design_contract"]["newsletters"]
  self.assertEqual((x["layout"],x["links"],x["graphic_logo"],x["hero_per_audience"]),("10_MODULES",13,True,True))
  self.assertEqual(x["cta_primary"],"#FF5F00")
 def test_welcome_vs_newsletter_independent(self):
  roles={f["role"] for f in self.x["legacy_flows"]}
  self.assertIn("LEAD_ACKNOWLEDGEMENT",roles)
  self.assertIn("LEGACY_NEWSLETTER_B2C",roles)
  self.assertEqual(self.x["new_newsletters"]["immediate_send_policy"].split(";")[0],
   "ON_VERIFIED_OPTIN_SEND_ONE_APPROVED_CURRENT_ISSUE_PER_CONTACT_PROFILE")
 def test_capture_missing_html_as_pending(self):
  self.assertIn("EXTRACT_FULL_LEGACY_HTML_AND_SETTINGS_BEFORE_CSS_CHANGES",self.x["blocking_gates"])
 def test_contract_for_all_customer_emails(self):
  d=self.x["homogeneous_design_contract"]["all_customer_emails"]
  self.assertTrue(all(d.values()))
if __name__=="__main__":unittest.main()

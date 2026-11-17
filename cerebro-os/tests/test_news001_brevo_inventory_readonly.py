import unittest,os,sys,json
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engines"/"CEREBRO-NEWS-001"))
import brevo_inventory_readonly as mod

def valid_data(name="FENIX PREPROD · Inmobiliarias",status=(False,True,None)):
  items=[{"id":24,"name":name},{"id":23,"name":"Hipoteca particulares"}]
  contacts=[{"email":"private"+str(i)+"@example.com","emailBlacklisted":v} for i,v in enumerate(status)]
  def reader(path):
    if path=="/account": return {"email":"secret@example.com","plan":[{"type":"free"}]}
    if path=="/senders": return {"senders":[{"email":"private@fenixcapital.es","active":True}]}
    if path=="/contacts/lists?limit=50&offset=0":return {"lists":items}
    if path=="/contacts/lists/24/contacts?limit=50&offset=0":return {"contacts":contacts}
    raise AssertionError("Unexpected endpoint "+path)
  return reader

class BrevoInspectorTests(unittest.TestCase):
  def test_only_readonly_paths(self):
    self.assertTrue(mod._allowed("/account"))
    self.assertFalse(mod._allowed("/contacts"))
    self.assertFalse(mod._allowed("/emailCampaigns"))
    self.assertFalse(mod._allowed("/contacts/lists/24"))
    self.assertFalse(mod._allowed("/contacts/lists/24/contacts?limit=50&offset=0&api-key=x"))
  def test_no_unsafe_external_urls(self):
    self.assertFalse(mod._allowed("https://api.attacker.invalid/account"))
  def test_b2b_historical_included_but_held(self):
    result=mod.inspect(valid_data())
    self.assertEqual(result["agency_lists"][0]["list_id"],24)
    self.assertEqual(result["agency_lists"][0]["environment"],"PREPROD_OR_TEST_HOLD")
    self.assertEqual(result["agency_lists"][0]["eligible_for_campaign"],0)
  def test_only_agencies_not_particulares(self):
    result=mod.inspect(valid_data())
    self.assertEqual(result["lists_without_inmobiliaria_term"],1)
    self.assertFalse(result["historical_particulares_imported"])
  def test_no_pii_output(self):
    result=json.dumps(mod.inspect(valid_data()),ensure_ascii=False)
    self.assertNotIn("private@",result);self.assertNotIn("secret@example.com",result)
  def test_aggregate_blocks(self):
    x=mod.inspect(valid_data())["agency_lists"][0]
    self.assertEqual((x["contacts_total"],x["not_email_blacklisted"],x["email_blacklisted"],x["blacklist_status_unknown"]),(3,1,1,1))
  def test_untrusted_count_not_automatically_eligible(self):
    x=mod.inspect(valid_data(status=(False,False,False)))["agency_lists"][0]
    self.assertEqual(x["not_email_blacklisted"],3);self.assertEqual(x["eligible_for_campaign"],0)
  def test_brand_sender_is_not_proof(self):
    x=mod.inspect(valid_data())
    self.assertEqual(x["senders_total"],1)
    self.assertFalse(x["send_authorized"])
  def test_account_free_is_not_actual_quota(self):
    x=mod.inspect(valid_data())
    self.assertIn("free",x["plans_reported"])
    self.assertFalse(x["account_quota_verified"])
  def test_unknown_format_denied(self):
    def bad(p):
      if p.startswith("/contacts/lists?"):return {"lists":[{"id":"24","name":"Inmobiliarias"}]}
      return valid_data()(p)
    with self.assertRaises(mod.InventoryBlocked):mod.inspect(bad)
  def test_missing_sender_data_denied(self):
    def bad(p):return {} if p=="/senders" else valid_data()(p)
    with self.assertRaises(mod.InventoryBlocked):mod.inspect(bad)
  def test_missing_contacts_list_denied(self):
    def bad(p):return {"garbage":[]} if "/24/contacts?" in p else valid_data()(p)
    with self.assertRaises(mod.InventoryBlocked):mod.inspect(bad)
  def test_duplicate_list_ids_denied(self):
    def bad(p):return {"lists":[{"id":24,"name":"Inmobiliarias"},{"id":24,"name":"Otros"}]} if p.startswith("/contacts/lists?") else valid_data()(p)
    with self.assertRaises(mod.InventoryBlocked):mod.inspect(bad)
  def test_nonprod_list_not_autoactive(self):
    x=mod.inspect(valid_data(name="CEREBRO NEWS · Inmobiliarias"))["agency_lists"][0]
    self.assertEqual(x["environment"],"PROD_NOT_YET_CERTIFIED")
    self.assertFalse(x["consent_evidence_verified"])
  def test_missing_env_flag_blocks(self):
    with patch.dict(os.environ,{"NEWS001_BREVO_READONLY_ENABLED":"false"},clear=True):
      self.assertEqual(mod.main(),2)
  def test_missing_secret_blocks(self):
    with patch.dict(os.environ,{"NEWS001_BREVO_READONLY_ENABLED":"true"},clear=True):
      self.assertEqual(mod.main(),2)
  def test_key_validation(self):
    with self.assertRaises(mod.InventoryBlocked):mod.make_reader("")
  def test_pagination_budget(self):
    def mock_get(p):
      if p.endswith("offset=0"):return {"lists":[{"id":i+1,"name":"misc"} for i in range(50)]}
      return {"lists":[]}
    self.assertEqual(len(mod._page(mock_get,"/contacts/lists?limit={limit}&offset={offset}","lists")),50)
  def test_no_mutating_methods_in_transport(self):
    self.assertNotIn("POST",open(mod.__file__,encoding="utf8").read().split("def make_reader")[1].split("def _page")[0])
if __name__=="__main__":unittest.main()

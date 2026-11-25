import unittest
from dataclasses import replace
from gateway.service import GatewayRequest
from gateway import catalog_read as c
from gateway.catalog_policy import evaluate_catalog_scope,offline_policy_callback
from governance.policy import PolicyRequest

class CatalogPolicy(unittest.TestCase):
    def setUp(self):
        self.req=GatewayRequest(c.COMPANY,c.ENGINE,c.CAPABILITY,c.ENV,c.VERSION)
        self.facts=PolicyRequest(c.COMPANY,c.COMPANY,c.ENV,c.CAPABILITY)
    def check(self,req=None,company=c.COMPANY,facts=None):
        return evaluate_catalog_scope(req or self.req,selected_company_id=company,facts=self.facts if facts is None else facts)
    def test_exact_contract(self):
        r=self.check()
        self.assertEqual(r["decision"],"ALLOW")
        self.assertFalse(r["runtime_identity_verified"])
    def test_no_company_or_alias(self):
        for x in (None,"","other","fenix-capital","FENIX_CAPITAL"):
            self.assertEqual(self.check(company=x)["decision"],"DENY")
    def test_no_prod_or_scope_change(self):
        for k,v in (("company_id","other"),("environment","PROD"),("engine_id","SUP-001"),("version","1.1.0"),("capability","FACT.INVENTORY.READ")):
            self.assertEqual(self.check(req=replace(self.req,**{k:v}))["decision"],"DENY")
    def test_context_scope(self):
        for k,v in (("target_company_id","other"),("company_id",None),("action","other"),("environment","PROD")):
            self.assertEqual(self.check(facts=replace(self.facts,**{k:v}))["decision"],"DENY")
    def test_no_writes(self):
        for k in ("irreversible","touches_prod"):
            self.assertEqual(self.check(facts=replace(self.facts,**{k:True}))["decision"],"DENY")
    def test_canonical_exceptions(self):
        for k,v,reason in (("legal_required",True,"LEGAL_REQUIRED"),("signature_required",True,"SIGNATURE_REQUIRED"),("confidence",0.5,"LOW_CONFIDENCE"),("risk","HIGH","HIGH_RISK"),("cost_eur",0.01,"MONEY_LIMIT"),("customer_human_request",True,"CUSTOMER_HUMAN_REQUEST")):
            r=self.check(facts=replace(self.facts,**{k:v}))
            self.assertEqual(r["decision"],"HUMAN_REQUIRED")
            self.assertIn(reason,r["reasons"])
    def test_invalid_facts(self):
        for k,v in (("confidence",float("nan")),("cost_eur",float("inf")),("money_limit_eur",1),("cost_eur",-1),("risk","UNKNOWN"),("legal_required",1)):
            self.assertEqual(self.check(facts=replace(self.facts,**{k:v}))["decision"],"DENY")
        self.assertEqual(self.check(facts={})["decision"],"DENY")
    def test_real_catalog_policy_composition(self):
        rows=[]
        cb=offline_policy_callback(selected_company_id=c.COMPANY,facts=self.facts)
        result=c.read_catalog(self.req,policy_check=cb,audit_sink=lambda r:(rows.append(r) or True))
        self.assertEqual(result["count"],177)
        self.assertEqual(len(rows),1)
        cb=offline_policy_callback(selected_company_id="other",facts=self.facts)
        result=c.read_catalog(self.req,policy_check=cb,audit_sink=lambda r:(rows.append(r) or True))
        self.assertNotIn("engine_ids",result)
        self.assertEqual(len(rows),1)

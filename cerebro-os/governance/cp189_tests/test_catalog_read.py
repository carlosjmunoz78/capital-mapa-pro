import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from gateway.service import GatewayRequest
from gateway import catalog_read as c
from registry.canonical_loader import canonical_engine_ids

class CatalogRead(unittest.TestCase):
    def setUp(self):
        self.req=GatewayRequest(c.COMPANY,c.ENGINE,c.CAPABILITY,c.ENV,c.VERSION)
        self.rows=[]
    def sink(self,r):
        self.rows.append(r);return True
    def run_read(self,r=None,policy=None,sink=None):
        return c.read_catalog(r or self.req,policy_check=policy or (lambda r:(True,None)),audit_sink=sink or self.sink)
    def test_real_catalog(self):
        x=self.run_read()
        self.assertEqual(x["status"],"CATALOG_READ")
        self.assertEqual(x["engine_ids"],canonical_engine_ids())
        self.assertEqual(len(set(x["engine_ids"])),177)
        self.assertFalse(x["operational_instances_certified"])
        self.assertFalse(x["deployment_authorized"])
        self.assertEqual(len(self.rows),1)
    def test_scope(self):
        for k,v in [("company_id","fenix-capital"),("engine_id","SUP-001"),("environment","PROD"),("environment","LAB"),("version","1.1.0"),("capability","FACT.INVENTORY.READ")]:
            self.assertEqual(self.run_read(replace(self.req,**{k:v}))["reason"],"SCOPE_DENIED")
        self.assertEqual(self.rows,[])
    def test_policy_denied(self):
        for v in [False,1,"ALLOW"]:
            self.assertEqual(self.run_read(policy=lambda r:(v,None))["reason"],"POLICY_OR_ROUTE_DENIED")
        self.assertEqual(self.rows,[])
    def test_missing_trust(self):
        x=c.read_catalog(self.req,policy_check=None,audit_sink=self.sink)
        self.assertEqual(x["reason"],"TRUSTED_RUNTIME_REQUIRED")
    def test_source_drift(self):
        with TemporaryDirectory() as d:
            p=Path(d)/"canonical_177.json";p.write_bytes(b"{}")
            with patch.object(c,"SOURCE",p):
                self.assertEqual(self.run_read()["reason"],"CATALOG_SOURCE_DRIFT")
        self.assertEqual(self.rows,[])
    def test_audit_failure_no_result(self):
        for sink in [lambda r:False,lambda r:None]:
            x=self.run_read(sink=sink)
            self.assertEqual(x["reason"],"AUDIT_UNCONFIRMED");self.assertNotIn("engine_ids",x)
        def broken(r):raise OSError("offline")
        self.assertNotIn("engine_ids",self.run_read(sink=broken))

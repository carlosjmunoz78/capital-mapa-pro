import unittest
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from console.persistent_store import ConsoleStore
from core.minimum.execute_catalog import AuthorizedContext,CatalogExecution
from gateway import catalog_read as c
from gateway.service import GatewayRequest
from governance.policy import PolicyRequest
from identity.contracts import Identity

class RuntimeComposition(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=ConsoleStore(Path(self.tmp.name)/"audit.sqlite")
        self.req=GatewayRequest(c.COMPANY,c.ENGINE,c.CAPABILITY,c.ENV,c.VERSION)
        self.ctx=AuthorizedContext(Identity("fixture:actor","MACHINE","fixture:owner",c.COMPANY,"fixture"),
            "fixture:001",c.ENGINE,c.ENV,c.VERSION,c.CAPABILITY,"fixture:grant",90,110,
            PolicyRequest(c.COMPANY,c.COMPANY,c.ENV,c.CAPABILITY))
        self.now=100
        self.enabled=True
        self.runtime=CatalogExecution(store=self.store,resolve_context=lambda _:self.ctx,
            execution_enabled=lambda:self.enabled,clock=lambda:self.now)
    def run_read(self,req=None,rid="fixture:001"):
        return self.runtime.execute(req or self.req,request_id=rid)
    def deny(self,result):
        self.assertEqual(result["status"],"BLOCKED")
        self.assertNotIn("engine_ids",result)
        self.assertFalse(result["deployment_authorized"])
    def empty(self):
        self.assertEqual(self.store.counts(),{"audit":0,"history":0})
    def test_exact_integration_and_replay(self):
        r=self.run_read();self.assertEqual(r["count"],177)
        self.assertEqual(self.run_read(),r)
        self.assertEqual(ConsoleStore(self.store.path).counts(),{"audit":1,"history":1})
    def test_wrong_scope(self):
        for k,v in (("company_id","other"),("environment","PROD"),("capability","WRITE")):
            self.deny(self.run_read(replace(self.req,**{k:v})))
        self.empty()
    def test_missing_or_untrusted_context(self):
        self.ctx=None;self.deny(self.run_read());self.empty()
    def test_context_scope_mismatch(self):
        self.ctx=replace(self.ctx,environment="PROD")
        self.deny(self.run_read());self.empty()
    def test_inactive_identity(self):
        self.ctx=replace(self.ctx,identity=replace(self.ctx.identity,status="REVOKED"))
        self.deny(self.run_read());self.empty()
    def test_identity_company_mismatch(self):
        self.ctx=replace(self.ctx,identity=replace(self.ctx.identity,company_id="other"))
        self.deny(self.run_read());self.empty()
    def test_expiry(self):
        self.now=110;self.deny(self.run_read());self.empty()
    def test_kill_switch(self):
        self.enabled=False;self.deny(self.run_read());self.empty()
    def test_policy_denied(self):
        self.ctx=replace(self.ctx,facts=replace(self.ctx.facts,risk="HIGH"))
        self.deny(self.run_read());self.empty()
    def test_request_mismatch(self):
        self.deny(self.run_read(rid="fixture:002"));self.empty()
    def test_missing_store(self):
        Path(self.store.path).unlink();self.deny(self.run_read())
        self.assertFalse(Path(self.store.path).exists())
    def test_unavailable_audit(self):
        with patch("core.minimum.execute_catalog.persist_catalog_audit",return_value=False):
            self.deny(self.run_read())
        self.empty()
    def test_revocation_before_audit(self):
        seq=iter([self.ctx,self.ctx,None])
        self.runtime=CatalogExecution(store=self.store,resolve_context=lambda _:next(seq),
            execution_enabled=lambda:True,clock=lambda:100)
        self.deny(self.run_read());self.empty()
    def test_revocation_before_release(self):
        seq=iter([self.ctx,self.ctx,self.ctx,None])
        self.runtime=CatalogExecution(store=self.store,resolve_context=lambda _:next(seq),
            execution_enabled=lambda:True,clock=lambda:100)
        self.deny(self.run_read())
        self.assertEqual(self.store.counts(),{"audit":1,"history":1})

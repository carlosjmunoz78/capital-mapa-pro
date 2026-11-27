import unittest,sqlite3,json
from pathlib import Path
from tempfile import TemporaryDirectory
from console.persistent_store import ConsoleStore
from core.minimum.execute_catalog import AuthorizedContext,CatalogExecution
from core.minimum.verify_execution import verify_execution
from gateway import catalog_read as c
from gateway.service import GatewayRequest
from governance.policy import PolicyRequest
from identity.contracts import Identity

class VerifyExecution(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"new.sqlite"
        self.store=ConsoleStore(self.path)
        self.ctx=AuthorizedContext(Identity("fixture:actor","MACHINE","fixture:owner",c.COMPANY,"fixture"),
            "fixture:verify",c.ENGINE,c.ENV,c.VERSION,c.CAPABILITY,"fixture:grant",90,110,
            PolicyRequest(c.COMPANY,c.COMPANY,c.ENV,c.CAPABILITY))
        runtime=CatalogExecution(store=self.store,resolve_context=lambda _:self.ctx,
            execution_enabled=lambda:True,clock=lambda:100)
        self.result=runtime.execute(GatewayRequest(c.COMPANY,c.ENGINE,c.CAPABILITY,c.ENV,c.VERSION),
            request_id=self.ctx.request_id)
        self.assertEqual(self.result["count"],177)
    def verify(self,**changes):
        args=dict(store_path=self.path,request_id=self.ctx.request_id,actor_id=self.ctx.identity.identity_id,
            result=self.result,now_epoch=100);args.update(changes)
        r=verify_execution(**args)
        self.assertFalse(r["deployment_authorized"])
        return r["status"]
    def test_actual_persistent_result(self):
        self.assertEqual(self.verify(),"ACCEPTANCE_READBACK_VERIFIED")
        self.assertEqual(self.store.counts(),{"audit":1,"history":1})
    def test_result_modified(self):
        self.assertEqual(self.verify(result={**self.result,"count":176}),"BLOCKED")
    def test_prod_label_rejected(self):
        self.assertEqual(self.verify(result={**self.result,"environment":"PROD"}),"BLOCKED")
    def test_wrong_actor(self):
        self.assertEqual(self.verify(actor_id="fixture:other"),"BLOCKED")
    def test_missing_request(self):
        self.assertEqual(self.verify(request_id="fixture:other"),"BLOCKED")
    def test_history_tampered(self):
        with sqlite3.connect(self.path) as db:db.execute("UPDATE console_history SET status='OTHER'")
        self.assertEqual(self.verify(),"BLOCKED")
    def test_metadata_tampered(self):
        with sqlite3.connect(self.path) as db:db.execute("UPDATE console_audit SET metadata_json='{}'")
        self.assertEqual(self.verify(),"BLOCKED")
    def test_missing_database_not_created(self):
        path=Path(self.tmp.name)/"missing.sqlite"
        self.assertEqual(self.verify(store_path=path),"BLOCKED");self.assertFalse(path.exists())
    def test_fresh_local_backup_readback(self):
        path=Path(self.tmp.name)/"fresh-test-backup.sqlite"
        with sqlite3.connect(self.path) as src,sqlite3.connect(path) as dst:src.backup(dst)
        self.assertEqual(self.verify(store_path=path),"ACCEPTANCE_READBACK_VERIFIED")
        self.assertEqual(self.verify(),"ACCEPTANCE_READBACK_VERIFIED")
    def test_future_timestamp(self):
        self.assertEqual(self.verify(now_epoch=99),"BLOCKED")

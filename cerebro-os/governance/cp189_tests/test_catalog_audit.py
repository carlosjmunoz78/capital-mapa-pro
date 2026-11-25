import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from gateway.service import GatewayRequest
from gateway import catalog_read as c
from gateway.catalog_audit import read_with_audit,persist_catalog_audit
from console.persistent_store import ConsoleStore

class CatalogAudit(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"catalog-rehearsal.sqlite"
        self.store=ConsoleStore(self.path)
        self.req=GatewayRequest(c.COMPANY,c.ENGINE,c.CAPABILITY,c.ENV,c.VERSION)
        self.kw=dict(store=self.store,request_id="fixture:catalog:001",user_id="fixture:actor",
                     now_epoch=100,policy_check=lambda r:(True,None))
    def read(self,**kwargs):
        return read_with_audit(self.req,**{**self.kw,**kwargs})
    def test_real_catalog_persist_and_reopen(self):
        self.assertEqual(self.read()["count"],177)
        self.assertEqual(ConsoleStore(self.path).counts(),{"audit":1,"history":1})
        self.assertEqual(self.store.history_by_company(c.COMPANY)[0]["status"],"CATALOG_READ")
        self.assertEqual(self.store.history_by_company("other"),())
    def test_exact_replay_is_idempotent(self):
        self.assertEqual(self.read()["status"],"CATALOG_READ")
        self.assertEqual(self.read(now_epoch=101)["status"],"CATALOG_READ")
        self.assertEqual(self.store.counts(),{"audit":1,"history":1})
    def test_different_actor_conflict(self):
        self.read()
        x=self.read(user_id="fixture:other")
        self.assertEqual(x["status"],"BLOCKED");self.assertNotIn("engine_ids",x)
        self.assertEqual(self.store.counts(),{"audit":1,"history":1})
    def test_same_scope_different_metadata_denied(self):
        self.read()
        with closing(sqlite3.connect(self.path)) as db:
            with db:db.execute("UPDATE console_audit SET metadata_json='{}'")
        self.assertNotIn("engine_ids",self.read())
    def test_history_drift_denied(self):
        self.read()
        with closing(sqlite3.connect(self.path)) as db:
            with db:db.execute("UPDATE console_history SET evidence_ref='different'")
        self.assertNotIn("engine_ids",self.read())
    def test_no_policy_no_write(self):
        self.assertEqual(self.read(policy_check=lambda r:(False,None))["status"],"BLOCKED")
        self.assertEqual(self.store.counts(),{"audit":0,"history":0})
    def test_missing_store_no_recreate(self):
        self.path.unlink()
        self.assertNotIn("engine_ids",self.read())
        self.assertFalse(self.path.exists())
    def test_invalid_context(self):
        for kwargs in [{"user_id":""},{"request_id":"invalid id"},{"now_epoch":True}]:
            self.assertNotIn("engine_ids",self.read(**kwargs))
        self.assertEqual(self.store.counts(),{"audit":0,"history":0})
    def test_store_failure(self):
        with patch.object(self.store,"record",side_effect=sqlite3.OperationalError("fixture fault")):
            self.assertNotIn("engine_ids",self.read())
        self.assertEqual(self.store.counts(),{"audit":0,"history":0})
    def test_new_catalog_audit_backup_reopen(self):
        # Only newly generated synthetic actor metadata in temporary local DB.
        self.assertEqual(self.read()["count"],177)
        backup=Path(self.tmp.name)/"backup.sqlite"
        with closing(sqlite3.connect(self.path.as_uri()+"?mode=ro",uri=True)) as src,closing(sqlite3.connect(backup)) as dst:
            src.backup(dst)
            self.assertEqual(dst.execute("PRAGMA integrity_check").fetchone(),("ok",))
        restored=ConsoleStore(backup)
        self.assertEqual(restored.counts(),{"audit":1,"history":1})
        self.assertEqual(self.read(store=restored,now_epoch=101)["status"],"CATALOG_READ")
        self.assertEqual(restored.counts(),self.store.counts())
        self.assertEqual(restored.audit_by_company(c.COMPANY),self.store.audit_by_company(c.COMPANY))

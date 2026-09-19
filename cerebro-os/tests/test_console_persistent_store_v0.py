import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"console"))

from persistent_store import ConsoleStore

class ConsolePersistentStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=ConsoleStore(Path(self.tmp.name)/"console.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def _audit(self,**overrides):
        row={
          "request_id":"req-1","user_id":"CARLOS","company_id":"fenix","context_type":"company",
          "environment":"LAB","version":"1.0.0","gateway_status":"ROUTED","engine_id":"COMP-ONB-001",
          "engine_status":"GREEN","action":"CREATE_COMPANY","result":"GREEN","evidence_ref":"e://1",
        }
        row.update(overrides)
        return row

    def test_record_is_persistent_and_company_scoped(self):
        self.store.record(self._audit(),now_epoch=100)
        self.assertEqual(self.store.counts(),{"audit":1,"history":1})
        self.assertEqual(self.store.audit_by_company("fenix")[0]["request_id"],"req-1")
        self.assertEqual(self.store.history_by_company("fenix")[0]["status"],"GREEN")
        self.assertEqual(self.store.audit_by_company("aion"),())

    def test_same_request_same_scope_is_idempotent_and_immutable(self):
        self.store.record(self._audit(),now_epoch=100)
        self.store.record(self._audit(result="BLOCKED"),now_epoch=200)
        self.assertEqual(self.store.counts(),{"audit":1,"history":1})
        self.assertEqual(self.store.audit_by_company("fenix")[0]["result"],"GREEN")
        self.assertEqual(self.store.audit_by_company("fenix")[0]["timestamp"],"100")

    def test_request_id_scope_conflict_is_denied(self):
        self.store.record(self._audit(),now_epoch=100)
        with self.assertRaisesRegex(PermissionError,"scope conflict"):
            self.store.record(self._audit(company_id="aion"),now_epoch=101)

    def test_raw_secret_fields_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"raw secret field"):
            self.store.record(self._audit(secret="never"),now_epoch=100)

if __name__=="__main__":
    unittest.main()

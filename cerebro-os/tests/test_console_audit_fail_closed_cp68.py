import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'console'))
from persistent_store import ConsoleStore
from runtime_builder import build_console_runtime


class ConsoleAuditCP68(unittest.TestCase):
    def audit(self):
        return {
          'request_id':'r-1','company_id':'fenix','user_id':'actor-synthetic',
          'environment':'LAB','version':'1.0.0',
          'engine_id':'COMP-ONB-001','action':'CREATE_COMPANY','result':'WAITING',
          'evidence_ref':'sha256:synthetic',
        }

    def test_sensitive_aliases_are_rejected_recursively(self):
        aliases=['access_token','accessToken','refresh-token','client_secret',
                 'clientSecret','privateKey','apiKey','set-cookie','session_cookie',
                 'authorizationHeader','BearerToken','api-token',
                 'authToken','id_token','oauth-token','serviceAccountKey','accessKey','jwt']
        with tempfile.TemporaryDirectory() as d:
            store=ConsoleStore(Path(d)/'audit.sqlite')
            for key in aliases:
                with self.subTest(key=key), self.assertRaisesRegex(ValueError,'raw secret field'):
                    store.record({**self.audit(), 'metadata':{'payload':[{key:'SYNTHETIC_SECRET'}]}},now_epoch=1)
            self.assertEqual(store.counts(), {'audit':0,'history':0})

    def test_authorization_header_bearer_is_rejected_but_status_is_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            store=ConsoleStore(Path(d)/'audit.sqlite')
            with self.assertRaisesRegex(ValueError,'raw secret field'):
                store.record({**self.audit(),'headers':{'Authorization':'Bearer SYNTHETIC'}},now_epoch=1)
            row={**self.audit(),'authorization':'GRANTED','secret_ref':'vault://synthetic',
                 'credential_ref_id':'cref-1','authorization_status':'VERIFIED'}
            store.record(row,now_epoch=2)
            self.assertEqual(store.counts(), {'audit':1,'history':1})

    def test_durable_audit_failure_does_not_create_phantom_memory_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            runtime=build_console_runtime(queue_path=Path(d)/'queue.sqlite',now_epoch_provider=lambda:100)
            with patch.object(runtime.store,'record',side_effect=sqlite3.OperationalError('synthetic io fail')):
                with self.assertRaisesRegex(sqlite3.OperationalError,'synthetic io fail'):
                    runtime.surface.pipeline.audit_sink(self.audit())
            self.assertEqual(runtime.audits,[])
            self.assertEqual(runtime.store.counts(),{'audit':0,'history':0})

    def test_successful_audit_persists_before_memory(self):
        with tempfile.TemporaryDirectory() as d:
            runtime=build_console_runtime(queue_path=Path(d)/'queue.sqlite',now_epoch_provider=lambda:101)
            runtime.surface.pipeline.audit_sink(self.audit())
            self.assertEqual(runtime.store.counts(),{'audit':1,'history':1})
            self.assertEqual(len(runtime.audits),1)
            self.assertEqual(runtime.audits[0]['request_id'],'r-1')

    def test_legacy_same_scope_replay_semantics_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            store=ConsoleStore(Path(d)/'audit.sqlite')
            store.record(self.audit(),now_epoch=100)
            store.record({**self.audit(),'result':'BLOCKED'},now_epoch=101)
            self.assertEqual(store.counts(),{'audit':1,'history':1})
            self.assertEqual(store.audit_by_company('fenix')[0]['result'],'WAITING')

    def test_tenant_id_conflict_still_denied(self):
        with tempfile.TemporaryDirectory() as d:
            store=ConsoleStore(Path(d)/'audit.sqlite')
            store.record(self.audit(),now_epoch=100)
            with self.assertRaises(PermissionError):
                store.record({**self.audit(),'company_id':'other'},now_epoch=101)
            self.assertEqual(store.counts(),{'audit':1,'history':1})

if __name__=='__main__':unittest.main()
import hashlib
import hmac
import json
import secrets
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Load exact sibling modules independently of the existing gateway.py module.
import importlib.util


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'gateway' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


make_trusted_grant_reader = load_module('iam_grant_reader_cp158', 'iam_grant_reader_cp158.py').make_trusted_grant_reader
verify_authorized_private_read = load_module('remote_read_proof_cp82_cp158', 'remote_read_proof_cp82.py').verify_authorized_private_read


class GrantReaderCP158(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'authority.sqlite'
        self.key = secrets.token_bytes(32)
        self.now = 1795395000
        self.ref = 'policy://cp158/fixture'
        self.state = dict(policy_receipt_ref=self.ref, issuer_id='iam-fixture',
            principal_id='jarvis-fixture', company_id='fenix-capital', request_id='cp158-local-0001',
            engine_id='FACT-001', environment='LAB', version='1.0.0',
            capability='FACT.INVENTORY.READ', decision='ALLOW_READ_ONLY', active=True,
            revoked=False, read_only=True, external_mutation_allowed=False, cost_ceiling_eur=0,
            issued_at_epoch=self.now-10, expires_at_epoch=self.now+120, checked_at_epoch=self.now)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE iam_grant_state(policy_receipt_ref TEXT PRIMARY KEY, grant_json TEXT NOT NULL, grant_mac TEXT NOT NULL)')
        self.publish(self.state)

    def mac(self, obj, key):
        return hmac.new(key, json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode(), hashlib.sha256).hexdigest()

    def publish(self, state, mac=None):
        with sqlite3.connect(self.path) as db:
            db.execute('INSERT OR REPLACE INTO iam_grant_state VALUES (?,?,?)',
                       (self.ref, json.dumps(state), mac or self.mac(state, self.key)))

    def reader(self, **kw):
        args = dict(authority_db=self.path, authority_key=self.key, issuer_id='iam-fixture',
                    principal_id='jarvis-fixture', company_id='fenix-capital', clock=lambda: self.now)
        args.update(kw)
        return make_trusted_grant_reader(**args)

    def test_current_signed_state(self):
        before = self.path.read_bytes()
        g = self.reader()(self.ref)
        self.assertTrue(g['verified'])
        self.assertEqual(g['request_id'], self.state['request_id'])
        self.assertNotIn('checked_at_epoch', g)
        self.assertEqual(before, self.path.read_bytes())

    def test_bad_signature_and_wrong_key(self):
        self.publish(self.state, '0'*64)
        with self.assertRaisesRegex(PermissionError, 'MAC_DENIED'):
            self.reader()(self.ref)
        self.publish(self.state)
        with self.assertRaisesRegex(PermissionError, 'MAC_DENIED'):
            self.reader(authority_key=secrets.token_bytes(32))(self.ref)

    def test_scope_and_alias_denied(self):
        for field, value in [('company_id','fenix'), ('principal_id','other'), ('issuer_id','other'), ('environment','PROD'), ('capability','FACT.WRITE'), ('engine_id','OTHER-001')]:
            with self.subTest(field=field):
                self.publish({**self.state, field:value})
                with self.assertRaisesRegex(PermissionError, 'SCOPE_DENIED'):
                    self.reader()(self.ref)

    def test_live_revocation_readback(self):
        read = self.reader()
        self.assertTrue(read(self.ref)['active'])
        self.publish({**self.state, 'revoked':True, 'active':False})
        with self.assertRaisesRegex(PermissionError, 'POLICY_DENIED'):
            read(self.ref)

    def test_freshness(self):
        for updates in [dict(checked_at_epoch=self.now-61), dict(checked_at_epoch=self.now+1), dict(expires_at_epoch=self.now), dict(expires_at_epoch=self.now+1000)]:
            with self.subTest(updates=updates):
                self.publish({**self.state, **updates})
                with self.assertRaisesRegex(PermissionError, 'FRESHNESS_DENIED'):
                    self.reader()(self.ref)

    def test_missing_or_invalid_ref(self):
        for ref in ('policy://missing/ref', "' OR 1=1 --"):
            with self.assertRaises(PermissionError):
                self.reader()(ref)

    def test_unavailable_database_not_created(self):
        missing = self.path.parent / 'missing.sqlite'
        with self.assertRaisesRegex(PermissionError, 'UNAVAILABLE'):
            self.reader(authority_db=missing)(self.ref)
        self.assertFalse(missing.exists())

    def test_no_unknown_fields_or_authority_self_assertion(self):
        for extra in ('token', 'verified', 'prod_authorized'):
            self.publish({**self.state, extra:True})
            with self.assertRaisesRegex(PermissionError, 'FIELDS_DENIED'):
                self.reader()(self.ref)

    def test_money_or_mutation_denied(self):
        for field,value in [('cost_ceiling_eur',1),('external_mutation_allowed',True),('read_only',False)]:
            self.publish({**self.state, field:value})
            with self.assertRaisesRegex(PermissionError, 'POLICY_DENIED'):
                self.reader()(self.ref)

    def test_cp131_real_sqlite_port_and_denied_storage(self):
        jkey, fkey = secrets.token_bytes(32), secrets.token_bytes(32)
        scope = {k:self.state[k] for k in ('request_id','company_id','engine_id','environment','version','capability','read_only','external_mutation_allowed','cost_ceiling_eur','principal_id','policy_receipt_ref')}
        scope.update(schema='cerebro.private-read.v1',emitted_at_epoch=self.now)
        j = dict(scope,origin='JARVIS',target='FACT-001',owner_access_verified=True,iam_policy='ALLOW_READ_ONLY')
        f = dict(scope,origin='FACT-001',target='JARVIS',status='COMPLETED',result_sha256='a'*64)
        touches=[]
        def persisted(ref):
            touches.append(ref)
            return f
        args=dict(jarvis=j,fact=f,jarvis_signature=self.mac(j,jkey),fact_signature=self.mac(f,fkey),jarvis_key=jkey,fact_key=fkey,company_id=self.state['company_id'],request_id=self.state['request_id'],now_epoch=self.now,persisted_fact_reader=persisted,trusted_grant_reader=self.reader(),expected_principal='jarvis-fixture',expected_issuer='iam-fixture',canonical_company_id=self.state['company_id'])
        self.assertEqual(verify_authorized_private_read(**args)['status'],'VERIFIED_AUTHORIZED_PAIR')
        self.assertEqual(len(touches),1)
        self.publish({**self.state,'revoked':True})
        with self.assertRaisesRegex(PermissionError,'POLICY_DENIED'):
            verify_authorized_private_read(**args)
        self.assertEqual(len(touches),1)

if __name__ == '__main__':
    unittest.main()

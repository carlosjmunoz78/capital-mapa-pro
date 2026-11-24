"""CP158: read-only CP131 port for authority-signed, current IAM snapshots.

The authority owns and updates the database. This module cannot issue or renew
identities, grants or credentials. Deployment and authority provenance are
separate acceptance gates; a local fixture never proves operational IAM.
"""
import hashlib
import hmac
import json
import re
import sqlite3
import time
from pathlib import Path

FIELDS = frozenset(('policy_receipt_ref', 'issuer_id', 'principal_id',
    'company_id', 'request_id', 'engine_id', 'environment', 'version',
    'capability', 'decision', 'active', 'revoked', 'read_only',
    'external_mutation_allowed', 'cost_ceiling_eur', 'issued_at_epoch',
    'expires_at_epoch', 'checked_at_epoch'))
REF = re.compile(r'[A-Za-z0-9_.:/-]{8,200}')
ID = re.compile(r'[A-Za-z0-9_.:-]{1,128}')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def make_trusted_grant_reader(*, authority_db, authority_key, issuer_id,
                              principal_id, company_id, clock=time.time,
                              max_state_age_s=60):
    """Bind trusted server configuration, never caller-supplied credentials.

    Authority-owned SQLite schema: iam_grant_state(policy_receipt_ref TEXT
    PRIMARY KEY, grant_json TEXT NOT NULL, grant_mac TEXT NOT NULL).
    Only the authority may publish signed current state, including revocation.
    A stale, inaccessible, invalid or ambiguous snapshot fails closed.
    """
    if type(authority_key) is not bytes or len(authority_key) < 32:
        raise ValueError('IAM_AUTHORITY_KEY_REQUIRED')
    if any(not isinstance(v, str) or not ID.fullmatch(v)
           for v in (issuer_id, principal_id, company_id)) or issuer_id == principal_id:
        raise ValueError('IAM_TRUST_SCOPE_REQUIRED')
    if type(max_state_age_s) is not int or not 1 <= max_state_age_s <= 60 or not callable(clock):
        raise ValueError('IAM_FRESHNESS_POLICY_REQUIRED')
    uri = Path(authority_db).resolve().as_uri() + '?mode=ro'

    def read(ref):
        if not isinstance(ref, str) or not REF.fullmatch(ref):
            raise PermissionError('IAM_REF_DENIED')
        try:
            with sqlite3.connect(uri, uri=True, timeout=1) as db:
                db.execute('PRAGMA query_only=ON')
                rows = db.execute('SELECT grant_json, grant_mac FROM iam_grant_state '
                                  'WHERE policy_receipt_ref=? LIMIT 2', (ref,)).fetchall()
        except sqlite3.Error:
            raise PermissionError('IAM_AUTHORITY_UNAVAILABLE') from None
        finally:
            # sqlite connection context manager does not close the connection.
            if 'db' in locals():
                db.close()
        if len(rows) != 1:
            raise PermissionError('IAM_STATE_MISSING_OR_AMBIGUOUS')
        raw, mac = rows[0]
        if not isinstance(raw, str) or len(raw) > 8192 or not isinstance(mac, str) or not re.fullmatch(r'[0-9a-f]{64}', mac):
            raise PermissionError('IAM_STATE_FORMAT_DENIED')
        try:
            state = json.loads(raw)
            expected = hmac.new(authority_key, _canonical(state), hashlib.sha256).hexdigest()
        except (ValueError, TypeError, OverflowError):
            raise PermissionError('IAM_STATE_FORMAT_DENIED') from None
        if not hmac.compare_digest(mac, expected):
            raise PermissionError('IAM_STATE_MAC_DENIED')
        if not isinstance(state, dict) or set(state) != FIELDS:
            raise PermissionError('IAM_STATE_FIELDS_DENIED')
        scope = dict(policy_receipt_ref=ref, issuer_id=issuer_id, principal_id=principal_id,
                     company_id=company_id, engine_id='FACT-001', environment='LAB',
                     capability='FACT.INVENTORY.READ', decision='ALLOW_READ_ONLY')
        if any(state[k] != v for k, v in scope.items()):
            raise PermissionError('IAM_STATE_SCOPE_DENIED')
        if not isinstance(state['request_id'], str) or not REF.fullmatch(state['request_id']) or not isinstance(state['version'], str) or not re.fullmatch(r'\d+\.\d+\.\d+', state['version']):
            raise PermissionError('IAM_STATE_SCOPE_DENIED')
        if (state['active'] is not True or state['revoked'] is not False or
            state['read_only'] is not True or state['external_mutation_allowed'] is not False or
            type(state['cost_ceiling_eur']) not in (int, float) or state['cost_ceiling_eur'] != 0):
            raise PermissionError('IAM_STATE_POLICY_DENIED')
        start, end, checked = (state[k] for k in ('issued_at_epoch', 'expires_at_epoch', 'checked_at_epoch'))
        now = int(clock())
        if (any(type(x) is not int for x in (start, end, checked)) or
            not 0 <= start <= checked <= now < end or not 0 < end-start <= 900 or
            now-checked > max_state_age_s):
            raise PermissionError('IAM_STATE_FRESHNESS_DENIED')
        return {**{k: v for k, v in state.items() if k != 'checked_at_epoch'}, 'verified': True}

    return read

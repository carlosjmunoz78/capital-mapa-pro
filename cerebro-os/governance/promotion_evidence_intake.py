"""Append-only admission of independently issued CP189 receipts.
This is the missing write-side, not a signer or release authority.
Trusted runtime supplies candidate, trust, clock and pre-provisioned DB path.
"""
import json
import sqlite3
from pathlib import Path
from dataclasses import asdict
from hashlib import sha256
from .promotion_gate import REQUIRED_GATES
from .verified_promotion_gate import Candidate
from .signed_promotion_receipts import signed_receipt_lookup
from .promotion_receipt_store import MAX_PAYLOAD, MAX_ENVELOPE, _unique_pairs

def admit_receipt(*, candidate, gate, evidence_id, payload, envelope_json,
                  store_path, trust, clock, max_age_seconds=3600):
    return _admit_receipt(candidate=candidate, gate=gate, evidence_id=evidence_id,
        payload=payload, envelope_json=envelope_json, store_path=store_path,
        trust=trust, clock=clock, max_age_seconds=max_age_seconds, expected_environment="PREPROD")


def admit_prod_receipt(*, candidate, gate, evidence_id, payload, envelope_json,
                       store_path, trust, clock, max_age_seconds=3600):
    """Trusted PROD evidence intake only. Requires a separately provisioned PROD store.
    This does not issue receipts, restore historical data or authorize a release.
    """
    return _admit_receipt(candidate=candidate, gate=gate, evidence_id=evidence_id,
        payload=payload, envelope_json=envelope_json, store_path=store_path,
        trust=trust, clock=clock, max_age_seconds=max_age_seconds, expected_environment="PROD")


def _admit_receipt(*, candidate, gate, evidence_id, payload, envelope_json,
                   store_path, trust, clock, max_age_seconds, expected_environment):
    def result(status, reason):
        return {"status":status,"reason":reason,"deployment_authorized":False}
    db=None
    try:
        if type(candidate) is not Candidate or candidate.environment!=expected_environment:
            return result("HOLD","CANDIDATE_SCOPE_DENIED")
        if gate not in REQUIRED_GATES or type(payload) is not bytes or not 0<len(payload)<=MAX_PAYLOAD:
            return result("HOLD","PAYLOAD_DENIED")
        if type(envelope_json) is not str or not 0<len(envelope_json.encode("utf-8"))<=MAX_ENVELOPE:
            return result("HOLD","ENVELOPE_DENIED")
        now=clock()
        if type(now) is not int or now<0:
            return result("HOLD","CLOCK_DENIED")
        envelope=json.loads(envelope_json,object_pairs_hook=_unique_pairs)
        lookup=signed_receipt_lookup(read_receipt=lambda g,e:envelope,
                                     trust=trust,clock=lambda:now,max_age_seconds=max_age_seconds)
        receipt=lookup(gate,evidence_id)
        if receipt is None or receipt.candidate!=candidate or receipt.payload_sha256!=sha256(payload).hexdigest():
            return result("HOLD","UNVERIFIED_RECEIPT")
        normalized=json.dumps(envelope,sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False)
        path=Path(store_path).resolve(strict=True)
        if not path.is_file():
            return result("HOLD","STORE_UNAVAILABLE")
        db=sqlite3.connect(path.as_uri()+"?mode=rw",uri=True,timeout=2)
        db.execute("PRAGMA trusted_schema=OFF")
        db.execute("BEGIN IMMEDIATE")
        scope_table=db.execute("SELECT type FROM sqlite_schema WHERE name='promotion_store_scope'").fetchall()
        if scope_table:
            if scope_table!=[("table",)] or db.execute("SELECT environment FROM promotion_store_scope LIMIT 2").fetchall()!=[(expected_environment,)]:
                db.rollback()
                return result("HOLD","STORE_SCOPE_DENIED")
        elif expected_environment=="PROD":
            db.rollback()
            return result("HOLD","STORE_SCOPE_DENIED")
        rows=db.execute("SELECT gate,payload,envelope FROM promotion_receipts WHERE evidence_id=? LIMIT 2",(evidence_id,)).fetchall()
        if rows:
            if len(rows)==1 and rows[0][0]==gate and rows[0][1]==payload and json.loads(rows[0][2],object_pairs_hook=_unique_pairs)==envelope:
                db.rollback()
                return result("ALREADY_ADMITTED","EXACT_RECEIPT_EXISTS")
            db.rollback()
            return result("HOLD","RECEIPT_ID_CONFLICT")
        db.execute("INSERT INTO promotion_receipts(gate,evidence_id,payload,envelope) VALUES(?,?,?,?)",(gate,evidence_id,payload,normalized))
        db.commit()
        return result("ADMITTED","SIGNED_RECEIPT_PERSISTED")
    except Exception:
        if db is not None:
            db.rollback()
        return result("HOLD","STORE_OR_TRUST_UNAVAILABLE")
    finally:
        if db is not None:
            db.close()

"""Read-only persistent receipt adapter for CP189. Never issues receipts or deploys."""
from pathlib import Path
import json
import sqlite3

from .promotion_gate import REQUIRED_GATES
from .signed_promotion_receipts import signed_receipt_lookup
from .verified_promotion_gate import decide_verified

MAX_PAYLOAD = 1048576
MAX_ENVELOPE = 16384

def _unique_pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("DUPLICATE_JSON_KEY")
        out[k] = v
    return out

def review_stored_candidate(*, candidate, receipt_ids, store_path, trust, clock,
                            policy_decision, human_required, max_age_seconds=3600):
    """Trusted runtime supplies path, keys, clock and policy; request supplies IDs only.
    A consistent read-only snapshot is used for both payload and signed envelope.
    No creation, signing, mutation, or promotion authority.
    """
    def blocked(reason):
        return {"decision":"BLOCKED","reason":reason,"missing":tuple(REQUIRED_GATES),
                "deployment_authorized":False}
    if type(receipt_ids) is not dict or set(receipt_ids) != set(REQUIRED_GATES):
        return blocked("GATE_SET_MISMATCH")
    conn = None
    try:
        now = clock()
        if type(now) is not int or now < 0:
            return blocked("INVALID_CLOCK")
        lookup_config = dict(trust)
        path = Path(store_path).resolve(strict=True)
        if not path.is_file():
            return blocked("RECEIPT_STORE_UNAVAILABLE")
        conn = sqlite3.connect(path.as_uri()+"?mode=ro", uri=True, timeout=1)
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA trusted_schema=OFF")
        conn.execute("BEGIN")
        evidence, envelopes = {}, {}
        for gate in REQUIRED_GATES:
            eid = receipt_ids[gate]
            if type(eid) is not str or not 8 <= len(eid) <= 128:
                continue
            rows = conn.execute(
                "SELECT payload, envelope FROM promotion_receipts "
                "WHERE gate=? AND evidence_id=? AND typeof(payload)='blob' "
                "AND length(payload) BETWEEN 1 AND ? AND typeof(envelope)='text' "
                "AND length(CAST(envelope AS BLOB)) BETWEEN 1 AND ? LIMIT 2",
                (gate,eid,MAX_PAYLOAD,MAX_ENVELOPE)).fetchall()
            if len(rows) != 1:
                continue
            payload, envelope = rows[0]
            try:
                envelope = json.loads(envelope, object_pairs_hook=_unique_pairs)
            except (ValueError,TypeError,RecursionError):
                continue
            evidence[gate] = {"id":eid,"payload":payload}
            envelopes[(gate,eid)] = envelope
        lookup = signed_receipt_lookup(read_receipt=lambda gate,eid: envelopes.get((gate,eid)),
                                      trust=lookup_config,clock=lambda:now,
                                      max_age_seconds=max_age_seconds)
        return decide_verified(candidate=candidate,
            gates={gate:gate in evidence for gate in REQUIRED_GATES},
            evidence={gate:evidence.get(gate,{}) for gate in REQUIRED_GATES},
            trusted_lookup=lookup,issuer_by_gate={g:v[0] for g,v in lookup_config.items()},
            now=now,policy_decision=policy_decision,human_required=human_required)
    except Exception:
        return blocked("RECEIPT_STORE_OR_TRUST_UNAVAILABLE")
    finally:
        if conn is not None:
            conn.close()

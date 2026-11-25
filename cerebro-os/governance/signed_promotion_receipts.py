"""Independent signed receipt lookup for the existing CP189 gate.
No receipt generation, no release authority and no network or secret access.
The runtime must provision trusted keys and an authoritative read-only receipt store.
"""
from dataclasses import asdict
from types import MappingProxyType
import json
import re
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .verified_promotion_gate import Candidate, TrustedEvidence
from .promotion_gate import REQUIRED_GATES

DOMAIN = b"cerebro.promotion.evidence.v1\x00"
FIELDS = {"schema", "gate", "candidate", "evidence_id", "payload_sha256", "issuer", "observed_at", "expires_at", "result"}
CANDIDATE_FIELDS = {"company_id", "engine_id", "environment", "version", "commit", "artifact_sha256"}

def canonical_receipt(body):
    return DOMAIN + json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")

def signed_receipt_lookup(*, read_receipt, trust, clock, max_age_seconds=3600):
    if not callable(read_receipt) or not callable(clock) or type(max_age_seconds) is not int or not 0 < max_age_seconds <= 86400:
        raise ValueError("INVALID_TRUST_CONFIG")
    if set(trust) != set(REQUIRED_GATES):
        raise ValueError("INCOMPLETE_TRUST_CONFIG")
    keys = {}
    for gate, pair in trust.items():
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError("INVALID_TRUST_ENTRY")
        issuer, raw = pair
        if not isinstance(issuer, str) or not issuer or type(raw) is not bytes or len(raw) != 32:
            raise ValueError("INVALID_TRUST_ENTRY")
        keys[gate] = (issuer, Ed25519PublicKey.from_public_bytes(raw), raw)
    # The independent tribunal cannot share the evidence-signing key of another gate.
    if any(keys["tribunal"][2] == v[2] for g, v in keys.items() if g != "tribunal"):
        raise ValueError("TRIBUNAL_KEY_NOT_INDEPENDENT")
    keys = MappingProxyType(keys)

    def lookup(gate, evidence_id):
        if gate not in keys or not isinstance(evidence_id, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,128}", evidence_id):
            return None
        try:
            envelope = read_receipt(gate, evidence_id)
            if type(envelope) is not dict or set(envelope) != {"body", "signature"}:
                return None
            b, sig = envelope["body"], envelope["signature"]
            # Copy only plain JSON-shaped data; the store cannot substitute the pinned key.
            if type(b) is not dict or set(b) != FIELDS or type(sig) is not str or not re.fullmatch(r"[a-f0-9]{128}", sig):
                return None
            c = b["candidate"]
            if type(c) is not dict or set(c) != CANDIDATE_FIELDS or any(type(v) is not str or not v for v in c.values()):
                return None
            if c["environment"] not in {"PREPROD", "PROD"} or not re.fullmatch(r"[a-f0-9]{40}", c["commit"]) or not re.fullmatch(r"[a-f0-9]{64}", c["artifact_sha256"]):
                return None
            issuer, key, _ = keys[gate]
            if b["schema"] != "cerebro.promotion.evidence.v1" or b["gate"] != gate or b["evidence_id"] != evidence_id or b["issuer"] != issuer or b["result"] != "PASS":
                return None
            if type(b["payload_sha256"]) is not str or not re.fullmatch(r"[a-f0-9]{64}", b["payload_sha256"]):
                return None
            observed, expires, t = b["observed_at"], b["expires_at"], clock()
            if any(type(x) is not int for x in (observed, expires, t)) or not (0 <= observed <= t < expires <= observed + max_age_seconds) or t-observed > max_age_seconds:
                return None
            key.verify(bytes.fromhex(sig), canonical_receipt(b))
            return TrustedEvidence(gate, Candidate(**c), evidence_id, b["payload_sha256"], issuer, observed, expires, "PASS")
        except Exception:
            return None
    return lookup

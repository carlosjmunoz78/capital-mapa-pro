"""Verify a candidate readback receipt using a separately provisioned tribunal key."""

import hashlib
import json
import re
import secrets

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from core.minimum.verify_execution import digest


DOMAIN = b"cerebro.catalog.readback.v1\x00"


def canonical_receipt(body):
    return DOMAIN + json.dumps(body, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False).encode("ascii")


def catalog_receipt_verifier(*, read_signed_receipt, issuer, public_key):
    """Bind an independent readback transport and its verification key at startup.

    The transport must read the durable audit/history independently before signing.
    This composition neither provisions a transport nor issues a key or a receipt.
    """
    if not callable(read_signed_receipt) or not isinstance(issuer, str) or not issuer:
        raise ValueError("AUDIT_RECEIPT_TRUST_REQUIRED")
    key = Ed25519PublicKey.from_public_bytes(public_key)

    def verify(*, context, result, clock):
        started_at = clock()
        expected = {
            "issuer": issuer,
            "nonce": secrets.token_hex(16),
            "request_id": context.request_id,
            "actor_id": context.identity.identity_id,
            "company_id": context.identity.company_id,
            "engine_id": context.engine_id,
            "environment": context.environment,
            "version": context.version,
            "capability": context.capability,
            "grant_ref": context.grant_ref,
            "source_sha256": result["source_sha256"],
            "result_sha256": digest(result),
            "status": "ACCEPTANCE_READBACK_VERIFIED",
        }
        try:
            envelope = read_signed_receipt(expected.copy(), result.copy())
            if type(envelope) is not dict or set(envelope) != {"body", "signature"}:
                return None
            body, signature = envelope["body"], envelope["signature"]
            if type(body) is not dict or set(body) != set(expected) | {"observed_at", "expires_at"}:
                return None
            if any(type(body[name]) is not str or body[name] != value for name, value in expected.items()):
                return None
            if type(signature) is not str or not re.fullmatch(r"[a-f0-9]{128}", signature):
                return None
            observed_at, expires_at, now = body["observed_at"], body["expires_at"], clock()
            if any(type(value) is not int for value in (started_at, observed_at, expires_at, now)) or not (
                context.issued_at <= started_at <= observed_at <= now < expires_at <= context.expires_at
            ):
                return None
            signed_bytes = canonical_receipt(body)
            signature_bytes = bytes.fromhex(signature)
            key.verify(signature_bytes, signed_bytes)
            return "sha256:" + hashlib.sha256(signature_bytes + signed_bytes).hexdigest()
        except Exception:
            return None

    return verify

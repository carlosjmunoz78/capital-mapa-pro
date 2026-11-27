"""Separate release authority for the existing CP189 review.
Internal candidate only. No network, deployment, credentials or hold clearance.
Trust and ledger must come from an independently provisioned control plane,
never a request. No live integration is asserted by this module.
"""
from dataclasses import asdict, dataclass
import json
import re
import sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from .prod_release_review import blocked, load_config, review, sha

DOMAIN = b"cerebro.release.approval.v1\x00"
HEX64 = re.compile(r"[a-f0-9]{64}")
ID = re.compile(r"[A-Za-z0-9_.:-]{8,128}")

@dataclass(frozen=True)
class ReleaseTrust:
    issuer: str
    public_key: bytes
    target: str
    active_holds: tuple
    hold_resolution_sha256: str
    ledger: Path

def canonical_approval(body):
    return DOMAIN + json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")

def authorize_release(raw, candidate_archive, evidence_archive, approval, *, trust, clock):
    """Reserve exactly one approved release. Does not deploy.
    Existing CP189 review remains unchanged and cannot authorize on its own.
    The executor must check reservation, expiry, exact target and archive hashes;
    a restored/stale ledger is not sufficient without independent fencing.
    """
    try:
        if type(trust) is not ReleaseTrust or type(trust.active_holds) is not tuple:
            return blocked("RELEASE_TRUST_UNAVAILABLE")
        if trust.active_holds:
            return blocked("ACTIVE_HOLDS")
        if (type(trust.hold_resolution_sha256) is not str or not HEX64.fullmatch(trust.hold_resolution_sha256)
                or type(trust.public_key) is not bytes or len(trust.public_key) != 32
                or type(trust.issuer) is not str or not ID.fullmatch(trust.issuer)
                or type(trust.target) is not str or not ID.fullmatch(trust.target)):
            return blocked("RELEASE_TRUST_INVALID")
        c, candidate, gate_trust = load_config(raw)
        if any(trust.issuer == issuer or trust.public_key == key for issuer, key in gate_trust.values()):
            return blocked("RELEASE_AUTHORITY_NOT_INDEPENDENT")
        if type(approval) is not dict or set(approval) != {"body", "signature"}:
            return blocked("RELEASE_APPROVAL_REQUIRED")
        body, signature = approval["body"], approval["signature"]
        if type(body) is not dict or type(signature) is not str or not re.fullmatch(r"[a-f0-9]{128}", signature):
            return blocked("RELEASE_APPROVAL_FORMAT")
        expected = {"schema": "cerebro.release.approval.v1", "decision": "APPROVE",
                    "issuer": trust.issuer, "candidate": asdict(candidate), "target": trust.target,
                    "artifact_id": c["artifact_id"], "evidence_artifact_id": c["evidence_artifact_id"],
                    "evidence_sha256": c["evidence_sha256"],
                    "hold_resolution_sha256": trust.hold_resolution_sha256,
                    "release_id": body.get("release_id"), "issued_at": body.get("issued_at"),
                    "expires_at": body.get("expires_at")}
        if body != expected or type(body["release_id"]) is not str or not ID.fullmatch(body["release_id"]):
            return blocked("RELEASE_APPROVAL_SCOPE")
        now, issued, expires = clock(), body["issued_at"], body["expires_at"]
        if any(type(v) is not int for v in (now, issued, expires)) or not 0 <= issued <= now < expires <= issued + 600:
            return blocked("RELEASE_APPROVAL_EXPIRED")
        Ed25519PublicKey.from_public_bytes(trust.public_key).verify(bytes.fromhex(signature), canonical_approval(body))
        result = review(raw, candidate_archive, evidence_archive, lambda: now)
        if result.get("decision") != "PROD_REVIEW_CANDIDATE" or result.get("deployment_authorized") is not False:
            return blocked("RELEASE_EVIDENCE_NOT_VERIFIED")
        # Reject mutation of archives while reviewing; the executor must rehash again.
        if sha(candidate_archive) != candidate.artifact_sha256 or sha(evidence_archive) != c["evidence_sha256"]:
            return blocked("RELEASE_ARCHIVE_CHANGED")
        if not now <= clock() < expires:
            return blocked("RELEASE_APPROVAL_EXPIRED")
        ledger = trust.ledger.resolve(strict=True)
        if not ledger.is_file():
            return blocked("RELEASE_LEDGER_UNAVAILABLE")
        # Ledger must have been provisioned independently. No auto-create/reset.
        with sqlite3.connect(ledger.as_uri() + "?mode=rw", uri=True, timeout=2) as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT environment FROM release_ledger_scope").fetchall() != [("PROD",)]:
                return blocked("RELEASE_LEDGER_SCOPE")
            if not now <= clock() < expires:
                return blocked("RELEASE_APPROVAL_EXPIRED")
            try:
                db.execute("INSERT INTO release_reservations (release_id,target,company_id,engine_id,commit_sha,artifact_sha256,evidence_sha256,expires_at) VALUES (?,?,?,?,?,?,?,?)",
                           (body["release_id"], trust.target, candidate.company_id, candidate.engine_id,
                            candidate.commit, candidate.artifact_sha256, c["evidence_sha256"], expires))
            except sqlite3.IntegrityError:
                return blocked("RELEASE_ALREADY_RESERVED")
        return {"decision": "RELEASE_RESERVED", "deployment_authorized": True,
                "release_id": body["release_id"], "target": trust.target,
                "candidate": asdict(candidate), "evidence_sha256": c["evidence_sha256"],
                "expires_at": expires, "deployed": False}
    except Exception:
        return blocked("RELEASE_AUTHORITY_UNAVAILABLE")

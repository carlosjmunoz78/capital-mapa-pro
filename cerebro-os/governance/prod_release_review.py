"""Read-only review of a new, independently signed PROD evidence package.
No deployment authority, no signing, no historical state import.
Configuration is supplied by the trusted repository administrator, not dispatch inputs.
"""
import base64
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import time
import zipfile
from pathlib import Path

from .policy import PolicyRequest, evaluate
from .promotion_gate import REQUIRED_GATES
from .promotion_evidence_intake import admit_prod_receipt
from .promotion_receipt_store import review_stored_candidate, _unique_pairs
from .verified_promotion_gate import Candidate

REPO = "carlosjmunoz78/capital-mapa-pro"
MAX_ARCHIVE = 32 * 1024 * 1024

def blocked(reason):
    return {"decision": "BLOCKED", "reason": reason, "deployment_authorized": False}

def load_config(raw):
    c = json.loads(raw, object_pairs_hook=_unique_pairs)
    if set(c) != {"candidate", "trust", "receipt_ids", "artifact_id", "evidence_artifact_id", "evidence_sha256"}:
        raise ValueError("CONFIG_FIELDS")
    candidate = Candidate(**c["candidate"])
    if candidate.environment != "PROD" or not re.fullmatch(r"[0-9a-f]{40}", candidate.commit):
        raise ValueError("CANDIDATE_SCOPE")
    if not re.fullmatch(r"[0-9a-f]{64}", candidate.artifact_sha256) or not re.fullmatch(r"[0-9a-f]{64}", c["evidence_sha256"]):
        raise ValueError("DIGEST")
    if any(type(c[k]) is not int or c[k] <= 0 for k in ("artifact_id", "evidence_artifact_id")) or c["artifact_id"] == c["evidence_artifact_id"]:
        raise ValueError("ARTIFACT_IDS")
    if set(c["trust"]) != set(REQUIRED_GATES) or set(c["receipt_ids"]) != set(REQUIRED_GATES):
        raise ValueError("GATE_SET")
    trust = {}
    for gate, entry in c["trust"].items():
        if set(entry) != {"issuer", "public_key_hex"} or not re.fullmatch(r"[0-9a-f]{64}", entry["public_key_hex"]):
            raise ValueError("TRUST")
        trust[gate] = (entry["issuer"], bytes.fromhex(entry["public_key_hex"]))
    return c, candidate, trust

def sha(path):
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_ARCHIVE:
        raise ValueError("ARCHIVE_SIZE")
    return hashlib.sha256(path.read_bytes()).hexdigest()

def review(raw, candidate_archive, evidence_archive, clock):
    try:
        c, candidate, trust = load_config(raw)
        if sha(candidate_archive) != candidate.artifact_sha256 or sha(evidence_archive) != c["evidence_sha256"]:
            return blocked("ARCHIVE_DIGEST_MISMATCH")
        now = clock()
        with zipfile.ZipFile(evidence_archive) as z:
            if z.namelist() != ["receipts.json"] or z.infolist()[0].file_size > MAX_ARCHIVE:
                return blocked("EVIDENCE_PACKAGE_FORMAT")
            bundle = json.loads(z.read("receipts.json"), object_pairs_hook=_unique_pairs)
        if set(bundle) != {"schema", "receipts"} or bundle["schema"] != "cerebro.prod.evidence.package.v1" or type(bundle["receipts"]) is not list or len(bundle["receipts"]) != len(REQUIRED_GATES):
            return blocked("EVIDENCE_PACKAGE_FORMAT")
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "review.sqlite"
            with sqlite3.connect(store) as db:
                db.execute("CREATE TABLE promotion_store_scope(environment TEXT NOT NULL)")
                db.execute("INSERT INTO promotion_store_scope VALUES('PROD')")
                db.execute("CREATE TABLE promotion_receipts(gate TEXT,evidence_id TEXT,payload BLOB,envelope TEXT,PRIMARY KEY(gate,evidence_id))")
            seen = set()
            for item in bundle["receipts"]:
                if set(item) != {"gate", "evidence_id", "payload_b64", "envelope"}:
                    return blocked("RECEIPT_FORMAT")
                gate = item["gate"]
                if gate not in REQUIRED_GATES or gate in seen or item["evidence_id"] != c["receipt_ids"][gate]:
                    return blocked("RECEIPT_SCOPE")
                seen.add(gate)
                outcome = admit_prod_receipt(candidate=candidate, gate=gate,
                    evidence_id=item["evidence_id"], payload=base64.b64decode(item["payload_b64"], validate=True),
                    envelope_json=json.dumps(item["envelope"]), store_path=store,
                    trust=trust, clock=lambda: now)
                if outcome["status"] != "ADMITTED":
                    return blocked("RECEIPT_NOT_ADMITTED:" + gate)
            # Local policy covers this read-only review, NOT the actual deployment.
            # The independent signed policy receipt remains mandatory in CP189.
            p = evaluate(PolicyRequest(candidate.company_id, candidate.company_id, "PROD", "PROD_RELEASE_REVIEW"))
            return review_stored_candidate(candidate=candidate, receipt_ids=c["receipt_ids"],
                store_path=store, trust=trust, clock=lambda: now,
                policy_decision=p["decision"], human_required=p["decision"] == "HUMAN_REQUIRED")
    except Exception:
        return blocked("CONFIG_OR_EVIDENCE_UNAVAILABLE")

def download(artifact_id, target):
    endpoint = f"repos/{REPO}/actions/artifacts/{artifact_id}"
    meta = json.loads(subprocess.check_output(["gh", "api", endpoint], timeout=30))
    if meta["id"] != artifact_id or meta["expired"] or not 0 < meta["size_in_bytes"] <= MAX_ARCHIVE:
        raise ValueError("ARTIFACT_UNAVAILABLE")
    with target.open("xb") as out:
        subprocess.run(["gh", "api", endpoint + "/zip"], stdout=out, check=True, timeout=60)
    sha(target)

def main():
    result = blocked("TRUSTED_CONFIG_NOT_PROVISIONED")
    try:
        raw = os.environ["CEREBRO_PROD_REVIEW_CONFIG"]
        c, _, _ = load_config(raw)
        if os.environ.get("GITHUB_REPOSITORY") != REPO:
            raise ValueError("REPOSITORY_SCOPE")
        with tempfile.TemporaryDirectory() as tmp:
            candidate, evidence = Path(tmp)/"candidate.zip", Path(tmp)/"evidence.zip"
            download(c["artifact_id"], candidate)
            download(c["evidence_artifact_id"], evidence)
            result = review(raw, candidate, evidence, lambda: int(time.time()))
    except Exception:
        pass
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "PROD_REVIEW_CANDIDATE" and result["deployment_authorized"] is False else 1

if __name__ == "__main__":
    raise SystemExit(main())

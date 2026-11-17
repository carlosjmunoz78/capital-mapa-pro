"""Fail-closed UMS-001 image quality gate. Delivery is NOT visual approval."""
from __future__ import annotations
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "quality" / "ums001_visual_rejections.json"
REQUIRED_CHECKS = ("anatomy_consistent", "limbs_connected", "hands_natural",
                   "faces_natural", "no_fake_text", "no_deformed_objects",
                   "scene_correct", "brand_appropriate", "rights_verified")
REVIEWER_ID = "UMS001-INDEPENDENT-VISION-QA-V1"

def _result(state, reasons, verified=False):
    passed = state == "REVIEWED_FOR_REUSE"
    return {"qa_state": state, "qa_reason_codes": reasons,
            "visual_qa": "PASS" if passed else ("REJECTED" if state == "REJECTED_VISUAL" else "PENDING"),
            "brand_qa": "PASS" if passed else "PENDING",
            "independent_vision_verified": verified, "reuse_allowed": passed,
            "visual_qc_required": True, "publish_authorized": False, "publication": False}

def assess_private_asset(*, asset_sha256, company_id, engine_id, request_id,
                         environment, attestation=None, reviewer_hmac_key=None):
    """Only a trusted, signed independent image review can unblock reuse."""
    if not re.fullmatch("[a-f0-9]{64}", asset_sha256 or ""):
        return _result("QA_HOLD", ["INVALID_SHA256"])
    try:
        policy = json.loads(REGISTRY.read_text(encoding="utf-8"))
        if policy.get("policy_id") != "UMS001-VISUAL-QA-FAIL-CLOSED-V1":
            raise ValueError("unknown policy")
    except (OSError, ValueError):
        return _result("QA_HOLD", ["QUALITY_POLICY_UNVERIFIED"])
    for item in policy.get("rejected_assets", []):
        if item.get("sha256") == asset_sha256:
            return _result("REJECTED_VISUAL", item.get("reason_codes", ["BLACKLISTED_ASSET"]))
    if environment != "LAB":
        return _result("QA_HOLD", ["ENVIRONMENT_DENIED"])
    if not isinstance(attestation, dict) or not isinstance(reviewer_hmac_key, bytes) or len(reviewer_hmac_key) < 32:
        return _result("QA_HOLD", ["INDEPENDENT_VISION_NOT_CERTIFIED"])
    payload, sig = attestation.get("payload"), attestation.get("hmac_sha256")
    if not isinstance(payload, dict) or not isinstance(sig, str):
        return _result("QA_HOLD", ["SIGNATURE_MISSING"])
    expected = hmac.new(reviewer_hmac_key,
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(),
        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return _result("QA_HOLD", ["INVALID_SIGNATURE"])
    identity = {"asset_sha256":asset_sha256, "company_id":company_id,
        "engine_id":engine_id,"request_id":request_id,"environment":environment,
        "reviewer_id":REVIEWER_ID}
    if any(payload.get(k) != v for k,v in identity.items()):
        return _result("QA_HOLD", ["REVIEW_IDENTITY_MISMATCH"])
    try:
        stamp = datetime.fromisoformat(payload["reviewed_at"].replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("missing timezone")
        age = (datetime.now(timezone.utc)-stamp.astimezone(timezone.utc)).total_seconds()
        if not -300 <= age <= 86400:
            raise ValueError("outdated")
    except (TypeError, ValueError, AttributeError, KeyError):
        return _result("QA_HOLD", ["REVIEW_EXPIRED_OR_INVALID"])
    checks = payload.get("checks")
    if not isinstance(checks, dict) or set(checks) != set(REQUIRED_CHECKS) or any(type(v) is not bool for v in checks.values()):
        return _result("QA_HOLD", ["INCOMPLETE_VISION_CHECKS"])
    confidence = payload.get("confidence")
    if type(confidence) not in (int,float) or not 0.92 <= confidence <= 1.0:
        return _result("QA_HOLD", ["LOW_CONFIDENCE"])
    bad = [k for k in REQUIRED_CHECKS if checks[k] is False]
    if bad:
        return _result("REJECTED_VISUAL", ["VISION_"+x.upper() for x in bad], True)
    return _result("REVIEWED_FOR_REUSE", [], True)

def require_reuse_approval(receipt):
    """Apply at any NEWS, social, WordPress, or other asset reuse boundary."""
    if not isinstance(receipt, dict) or not (
        receipt.get("qa_state") == "REVIEWED_FOR_REUSE"
        and receipt.get("reuse_allowed") is True
        and receipt.get("independent_vision_verified") is True
        and receipt.get("visual_qa") == "PASS"
        and receipt.get("brand_qa") == "PASS"):
        raise PermissionError("UMS001_VISUAL_QA_NOT_APPROVED_FOR_REUSE")

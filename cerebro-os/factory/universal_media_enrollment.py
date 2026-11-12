"""FACT-001 -> UMS-001 universal media enrollment. One shared signed queue, no per-engine wiring."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENGINE_RE = re.compile(r"^[A-Z][A-Z0-9-]{2,63}$")
COMPANY_RE = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
DEFAULT_SCOPES = ("GENERIC",)
EVENT_NAME = "FACT001_ENGINE_CREATED"


def _atomic_record(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_enrollment_event(manifest: dict, company_id: str, issued_at_utc: str | None = None) -> dict:
    engine = str(manifest.get("engine_id", ""))
    if not ENGINE_RE.fullmatch(engine) or not COMPANY_RE.fullmatch(company_id):
        raise ValueError("factory scope is invalid")
    if manifest.get("environment") != "LAB" or company_id != "fenix":
        raise ValueError("only explicitly scoped fenix LAB enrollment is currently authorized")
    version = manifest.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("invalid manifest version")
    cap = manifest.get("media_gateway", {})
    if cap.get("provider_engine_id") != "UMS-001" or "IMAGE.SYNTHETIC" not in cap.get("capabilities", []):
        raise ValueError("universal media capability unavailable")
    allowed = cap.get("allowed_channels") or list(DEFAULT_SCOPES)
    if not isinstance(allowed, list) or not allowed or any(c not in {
        "SEO", "GENERIC", "FACEBOOK", "INSTAGRAM", "LINKEDIN", "YOUTUBE", "TIKTOK"
    } for c in allowed):
        raise ValueError("invalid channels")
    event_hash = hashlib.sha256(
        f"{company_id}/{manifest['environment']}/{engine}/{version}".encode("ascii")
    ).hexdigest()[:32].upper()
    issued = issued_at_utc or datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return {
        "schema_version": 1,
        "event_type": EVENT_NAME,
        "event_id": "FACT-ENROLL-" + event_hash,
        "company_id": company_id,
        "engine_id": engine,
        "environment": "LAB",
        "version": version,
        "allowed_channels": allowed,
        "media_capabilities": ["IMAGE.SYNTHETIC"],
        "issued_at_utc": issued,
    }


def _signed_payload(event: dict, secret: str) -> dict:
    if len(secret) < 48:
        raise ValueError("enrollment signing key missing or too short")
    canonical = json.dumps(event, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).digest()
    return {**event, "signature": base64.b64encode(signature).decode("ascii")}


def enroll_factory_engine(
    target: Path, manifest: dict, company_id: str | None = None,
    *, environ: dict | None = None, transport=None,
) -> dict:
    env = dict(os.environ if environ is None else environ)
    scope = company_id or env.get("CEREBRO_COMPANY_ID")
    receipt_path = target / "events" / "UMS001_FACTORY_ENROLLMENT_STATUS.json"
    if not scope:
        status = {"status": "PENDING_COMPANY_IAM", "media_dispatch_enabled": False}
        _atomic_record(receipt_path, status)
        return status
    try:
        event = build_enrollment_event(manifest, scope)
    except ValueError:
        status = {"status": "HOLD_INVALID_FACTORY_SCOPE", "media_dispatch_enabled": False}
        _atomic_record(receipt_path, status)
        return status
    _atomic_record(target / "events" / "FACT001_ENGINE_CREATED.outbox.json", event)
    key = env.get("CEREBRO_FACT_ENROLL_EVENT_KEY", "")
    api_token = env.get("CEREBRO_CLOUDFLARE_API_TOKEN", "")
    account_id = env.get("CEREBRO_CLOUDFLARE_ACCOUNT_ID", "")
    queue_id = env.get("CEREBRO_FACT_ENROLL_QUEUE_ID", "")
    if not all((key, api_token, account_id, queue_id)):
        status = {"status": "PENDING_FACTORY_IAM_TRANSPORT", "event_id": event["event_id"],
                  "company_id": scope, "engine_id": manifest["engine_id"],
                  "media_dispatch_enabled": False}
        _atomic_record(receipt_path, status)
        return status
    if not re.fullmatch(r"[0-9a-f]{32}", account_id) or not re.fullmatch(r"[0-9a-f]{32}", queue_id):
        status = {"status": "HOLD_INVALID_TRANSPORT_CONFIG", "event_id": event["event_id"],
                  "media_dispatch_enabled": False}
        _atomic_record(receipt_path, status)
        return status
    body = json.dumps({"content_type": "json", "body": _signed_payload(event, key)},
                      separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/queues/{queue_id}/messages"
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Authorization": "Bearer " + api_token, "Content-Type": "application/json"},
    )
    try:
        opener = transport or urllib.request.urlopen
        with opener(req, timeout=8) as response:
            reply = json.loads(response.read().decode("utf-8"))
        if reply.get("success") is not True:
            raise RuntimeError("Cloudflare queue did not accept enrollment")
        status = {"status": "QUEUED_SIGNED_ENROLLMENT_PENDING_GATEWAY_ACK",
                  "event_id": event["event_id"], "engine_id": manifest["engine_id"],
                  "company_id": scope, "media_dispatch_enabled": False}
    except Exception:
        # No network retries or secret values in persistent files and CI logs.
        status = {"status": "HOLD_ENROLLMENT_TRANSPORT", "event_id": event["event_id"],
                  "engine_id": manifest["engine_id"], "media_dispatch_enabled": False}
    _atomic_record(receipt_path, status)
    return status

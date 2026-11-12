"""FACT-001 · Universal image capability scaffold (additive, no network activity).

New engines declare an event bus contract to UMS-001. The trusted FACT-001
runtime must enroll the engine key in CEREBRO Gateway before dispatch is allowed.
"""
from __future__ import annotations

import json
from pathlib import Path

MEDIA_REQUEST_EVENT = "MEDIA_JOB_REQUESTED"
MEDIA_RESULT_EVENTS = ["UMS001_ORDER_ACCEPTED", "UMS001_ASSET_QA_PENDING", "MEDIA_JOB_COMPLETED"]


def media_manifest(engine: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "company_id": "RESOLVED_FROM_SIGNED_FACTORY_CONTEXT",
        "engine_id": engine["engine_id"],
        "environment": engine["environment"],
        "version": engine["version"],
        "capability_provider": "UMS-001",
        "gateway": "CEREBRO_GATEWAY_UNIVERSAL",
        "enrollment": "AUTO_ON_CREATE_VIA_TRUSTED_FACTORY_IAM",
        "enrollment_status": "PENDING_FACTORY_IAM",
        "request_event": MEDIA_REQUEST_EVENT,
        "response_events": MEDIA_RESULT_EVENTS,
        "media_capabilities": ["IMAGE.SYNTHETIC"],
        "security": {
            "signed_identity_required": True,
            "registry_allowlist_required": True,
            "tenant_isolation_required": True,
            "no_payload_asserted_identity": True,
            "replay_protection_required": True,
            "publish_authorized": False,
            "paid_execution_enabled": False,
        },
        "transport": {
            "source": "CEREBRO_GATEWAY",
            "uses_per_engine_worker": False,
            "uses_per_engine_queue": False,
            "shared_runtime": True,
        },
    }


def write_universal_media_scaffold(target: Path, engine: dict) -> None:
    config = media_manifest(engine)
    (target / "config" / "ums001_universal_media.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (target / "events" / "MEDIA_JOB_REQUESTED.contract.json").write_text(
        json.dumps({
            "event_type": MEDIA_REQUEST_EVENT, "schema_version": "1.0.0",
            "origin_engine_id": engine["engine_id"],
            "company_id": "TRUSTED_FACTORY_SCOPE",
            "environment": engine["environment"],
            "requires": ["request_id", "item_id", "capability_id", "brief_ref", "format", "budget"],
            "reply_to": "cerebro://events/ums001",
            "dispatch_enabled": False,
            "blocked_until": ["FACTORY_SIGNED_ENROLLMENT", "IAM_REGISTERED", "CAPABILITY_ALLOWED"],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

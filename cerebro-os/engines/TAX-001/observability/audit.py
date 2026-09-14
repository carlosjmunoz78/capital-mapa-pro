from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

ENGINE_ID = "TAX-001"
VERSION = "0.1.0"
ENVIRONMENT = "LAB"


def build_audit_event(payload: dict[str, Any], result: dict[str, Any], *, duration_ms: int = 0) -> dict[str, Any]:
    """Build a serializable audit event. Persistence is delegated to AUD-001."""
    return {
        "event_type": "tax.decision_support.audited",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "request_id": str(payload.get("request_id", "")),
        "company_id": str(payload.get("company_id", "")),
        "engine_id": ENGINE_ID,
        "version": VERSION,
        "environment": ENVIRONMENT,
        "operation": str(payload.get("operation", "")).upper(),
        "result": result.get("status"),
        "human_required": result.get("human_required"),
        "rule_id": result.get("rule_id"),
        "rule_version": result.get("rule_version"),
        "evidence_refs": list(result.get("evidence_refs") or []),
        "corpus_lock_verified": bool(result.get("corpus_lock_verified", False)),
        "duration_ms": int(duration_ms),
        "cost_eur": float(result.get("cost_eur", 0.0)),
        "persistence_status": "NOT_PERSISTED_BY_TAX001",
        "persistence_owner": "AUD-001",
    }


def persist_audit_event(event: dict[str, Any], sink: Any) -> dict[str, Any]:
    """Persist through an injected AUD-001-compatible sink without coupling TAX-001 to storage."""
    persist = getattr(sink, "persist", None)
    if not callable(persist):
        raise TypeError("sink must expose persist(event)")
    return persist(event)

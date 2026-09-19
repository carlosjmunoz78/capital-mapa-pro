from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

VALID_STATES = {"ACTIVE", "STALE_REVIEW", "SUPERSEDED", "RETIRED_REFERENCE_ONLY"}
PROTECTED_KINDS = {"POLICY", "LEGAL_RULE", "PERMISSION", "SECURITY_CONTROL"}


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _confidence_after_decay(confidence: float, age_days: int, ttl_days: int) -> float:
    if age_days <= ttl_days:
        return max(0.0, min(1.0, confidence))
    overdue = age_days - ttl_days
    decay = min(0.60, overdue / max(ttl_days, 1) * 0.20)
    return round(max(0.0, min(1.0, confidence - decay)), 4)


def analyze_record(record: dict, now: datetime) -> dict:
    company_id = str(record.get("company_id", "")).strip()
    knowledge_id = str(record.get("knowledge_id", "")).strip()
    environment = str(record.get("environment", "")).strip()
    version = str(record.get("version", "")).strip()
    kind = str(record.get("kind", "KNOWLEDGE")).strip().upper()
    if not all((company_id, knowledge_id, environment, version)):
        raise ValueError("complete knowledge scope required")

    state = str(record.get("state", "ACTIVE")).strip().upper()
    if state not in VALID_STATES:
        raise ValueError("invalid knowledge state")

    verified_at_raw = str(record.get("verified_at", "")).strip()
    if not verified_at_raw:
        raise ValueError("verified_at required")
    verified_at = _parse_ts(verified_at_raw)
    age_days = max(0, int((now - verified_at).total_seconds() // 86400))
    ttl_days = int(record.get("ttl_days", 90))
    if ttl_days < 1:
        raise ValueError("ttl_days must be >= 1")
    confidence = float(record.get("confidence", 1.0))
    if confidence < 0 or confidence > 1:
        raise ValueError("confidence must be between 0 and 1")

    superseded_by = str(record.get("superseded_by", "")).strip()
    contradictory_evidence = bool(record.get("contradictory_evidence", False))
    source_available = bool(record.get("source_available", True))
    protected = kind in PROTECTED_KINDS

    reasons: list[str] = []
    next_state = state
    proposed_confidence = _confidence_after_decay(confidence, age_days, ttl_days)

    if superseded_by:
        next_state = "SUPERSEDED"
        reasons.append("SUPERSEDED_BY_NEWER_EVIDENCE")
    elif contradictory_evidence:
        next_state = "STALE_REVIEW"
        reasons.append("CONTRADICTORY_EVIDENCE")
    elif age_days > ttl_days:
        next_state = "STALE_REVIEW"
        reasons.append("TTL_EXPIRED")
    elif not source_available:
        next_state = "STALE_REVIEW"
        reasons.append("SOURCE_UNAVAILABLE")

    if protected and next_state != "ACTIVE":
        reasons.append("PROTECTED_KIND_REQUIRES_HUMAN_OR_POLICY_REVIEW")

    return {
        "company_id": company_id,
        "knowledge_id": knowledge_id,
        "environment": environment,
        "version": version,
        "kind": kind,
        "provenance_id": str(record.get("provenance_id", "")).strip(),
        "source_type": str(record.get("source_type", "")).strip().upper(),
        "source_uri": str(record.get("source_uri", "")).strip(),
        "previous_state": state,
        "proposed_state": next_state,
        "previous_confidence": confidence,
        "proposed_confidence": proposed_confidence,
        "age_days": age_days,
        "ttl_days": ttl_days,
        "reasons": reasons,
        "delete_allowed": False,
        "history_preserved": True,
        "automatic_forgetting_allowed": False,
        "policy_or_permission_change_allowed": False,
        "external_mutation_allowed": False,
        "human_review_required": protected and next_state != "ACTIVE",
        "review_required": next_state != "ACTIVE",
    }


def run() -> list[Path]:
    source_root = Path(os.environ.get(
        "CEREBRO_KNOWLEDGE_INVENTORY_ROOT",
        ".cerebro-runtime/knowledge-inventory",
    ))
    out_root = Path(os.environ.get(
        "CEREBRO_OBSOLESCENCE_ROOT",
        ".cerebro-runtime/obsolescence",
    ))
    out_root.mkdir(parents=True, exist_ok=True)
    now_raw = os.environ.get("CEREBRO_OBSOLESCENCE_NOW")
    now = _parse_ts(now_raw) if now_raw else datetime.now(timezone.utc)
    written: list[Path] = []

    for path in sorted(source_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else [payload]
        decisions = [analyze_record(item, now) for item in records]
        company_ids = {item["company_id"] for item in decisions}
        if len(company_ids) != 1:
            raise ValueError("cross-company knowledge inventory denied")
        company_id = next(iter(company_ids))
        target = out_root / f"{company_id}.json"
        target.write_text(json.dumps({
            "record_type": "knowledge_obsolescence_review",
            "company_id": company_id,
            "generated_at": now.isoformat(),
            "status": "REVIEW_READY",
            "history_preserved": True,
            "delete_allowed": False,
            "external_mutation_allowed": False,
            "decisions": decisions,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        written.append(target)
    return written


if __name__ == "__main__":
    for path in run():
        print(path)

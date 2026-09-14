from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("event_type", "occurred_at", "request_id", "company_id", "engine_id", "version", "environment", "result")


def validate_event(event: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not str(event.get(field, "")).strip()]
    if missing:
        raise ValueError(f"missing audit fields: {', '.join(missing)}")
    if event.get("persistence_owner") not in (None, "AUD-001"):
        raise ValueError("audit event persistence_owner must be AUD-001")


class JsonlAuditSink:
    """Zero-cost LAB sink. Append-only and partitioned by company/environment."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def persist(self, event: dict[str, Any]) -> dict[str, Any]:
        validate_event(event)
        company_id = str(event["company_id"])
        environment = str(event["environment"])
        engine_id = str(event["engine_id"])
        target = self.root / company_id / environment / f"{engine_id}.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        record = dict(event)
        record["persistence_status"] = "PERSISTED"
        record["persistence_owner"] = "AUD-001"
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
        return {"status": "PERSISTED", "path": str(target), "record": record}

from __future__ import annotations

import json
from pathlib import Path

VALID_STATUS = {
    "CONFIRMED_OPERATIONAL",
    "DOCUMENTED_PARTIAL",
    "DEFINED_NOT_BUILT",
    "PROPOSED",
    "UNKNOWN_REQUIRES_AUDIT",
}
VALID_SCOPE = {"GLOBAL_ONLY", "GLOBAL_OR_SCOPED", "COMPANY_SCOPED"}


def load_registry(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("registry must be a list")
    validate_registry(data)
    return data


def validate_registry(items: list[dict]) -> None:
    seen: set[str] = set()
    required = {"engine_id", "name", "status", "version", "environment", "company_scope"}
    for item in items:
        missing = required - item.keys()
        if missing:
            raise ValueError(f"missing fields for registry item: {sorted(missing)}")
        engine_id = item["engine_id"]
        if engine_id in seen:
            raise ValueError(f"duplicate engine_id: {engine_id}")
        seen.add(engine_id)
        if item["status"] not in VALID_STATUS:
            raise ValueError(f"invalid status for {engine_id}: {item['status']}")
        if item["company_scope"] not in VALID_SCOPE:
            raise ValueError(f"invalid company_scope for {engine_id}: {item['company_scope']}")
        if item["environment"] not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError(f"invalid environment for {engine_id}: {item['environment']}")

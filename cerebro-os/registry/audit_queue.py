from __future__ import annotations

PRIORITY = {
    "BLOCKED": 0,
    "HUMAN_REQUIRED": 1,
    "UNKNOWN_REQUIRES_AUDIT": 2,
    "DOCUMENTED_PARTIAL": 3,
    "DEFINED_NOT_BUILT": 4,
    "LAB_GREEN": 5,
    "CONFIRMED_OPERATIONAL": 6,
}


def build_audit_queue(matrix) -> tuple[dict, ...]:
    rows = []
    for row in matrix:
        state = row.get("state", "UNKNOWN_REQUIRES_AUDIT")
        if state not in PRIORITY:
            raise ValueError(f"unknown readiness state: {state}")
        if state in {"LAB_GREEN", "CONFIRMED_OPERATIONAL"}:
            continue
        rows.append({
            "engine_id": row["engine_id"],
            "state": state,
            "priority": PRIORITY[state],
        })
    return tuple(sorted(rows, key=lambda item: (item["priority"], item["engine_id"])))

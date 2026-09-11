from __future__ import annotations

PRIORITY = {
    "BLOCKED": 0,
    "HUMAN_REQUIRED": 1,
    "UNKNOWN_REQUIRES_AUDIT": 2,
    "DOCUMENTED_PARTIAL": 3,
    "DEFINED_NOT_BUILT": 4,
}


def select_next_engine(matrix) -> dict | None:
    candidates = []
    for row in matrix:
        state = row.get("state", "UNKNOWN_REQUIRES_AUDIT")
        if state in {"LAB_GREEN", "CONFIRMED_OPERATIONAL"}:
            continue
        if state not in PRIORITY:
            raise ValueError(f"unsupported state: {state}")
        candidates.append((PRIORITY[state], row["engine_id"], row))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item[0], item[1]))[0][2]


def next_action(row: dict) -> dict:
    state = row.get("state", "UNKNOWN_REQUIRES_AUDIT")
    engine_id = row.get("engine_id")
    if not engine_id:
        raise ValueError("engine_id required")
    if state == "BLOCKED":
        return {"engine_id": engine_id, "action": "BLOCKED", "auto": False}
    if state == "HUMAN_REQUIRED":
        return {"engine_id": engine_id, "action": "HUMAN_REQUIRED", "auto": False}
    if state == "UNKNOWN_REQUIRES_AUDIT":
        return {"engine_id": engine_id, "action": "AUDIT", "auto": True}
    if state in {"DOCUMENTED_PARTIAL", "DEFINED_NOT_BUILT"}:
        return {"engine_id": engine_id, "action": "GAP_ANALYSIS", "auto": True}
    if state in {"LAB_GREEN", "CONFIRMED_OPERATIONAL"}:
        return {"engine_id": engine_id, "action": "SKIP_GREEN", "auto": True}
    raise ValueError(f"unsupported state: {state}")


def gap_plan(*, engine_id: str, missing: tuple[str, ...] | list[str], auto_safe: set[str]) -> dict:
    safe = tuple(item for item in missing if item in auto_safe)
    review = tuple(item for item in missing if item not in auto_safe)
    return {
        "engine_id": engine_id,
        "safe_autofix": safe,
        "review_required": review,
        "next": "SAFE_AUTOFIX" if safe else ("REVIEW_REQUIRED" if review else "TEST_REQUIRED"),
    }

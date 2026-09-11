from __future__ import annotations

GREEN_STATES = {"LAB_GREEN", "CONFIRMED_OPERATIONAL"}


def system_readiness(*, canonical_ids, matrix) -> dict:
    canonical = tuple(canonical_ids)
    if len(canonical) != 177 or len(set(canonical)) != 177:
        raise ValueError("system gate requires exactly 177 unique canonical engines")
    by_id = {row["engine_id"]: row for row in matrix}
    missing_rows = tuple(engine_id for engine_id in canonical if engine_id not in by_id)
    not_green = tuple(
        engine_id for engine_id in canonical
        if engine_id in by_id and by_id[engine_id].get("state") not in GREEN_STATES
    )
    green_count = len(canonical) - len(missing_rows) - len(not_green)
    return {
        "state": "GREEN" if not missing_rows and not not_green else "RED",
        "total": len(canonical),
        "green_count": green_count,
        "missing_rows": missing_rows,
        "not_green": not_green,
    }

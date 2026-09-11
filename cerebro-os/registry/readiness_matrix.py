from __future__ import annotations

DEFAULT_STATE = "UNKNOWN_REQUIRES_AUDIT"


def build_readiness_matrix(*, canonical_ids, live_records: list[dict] | tuple[dict, ...]) -> tuple[dict, ...]:
    canonical = tuple(canonical_ids)
    if len(canonical) != len(set(canonical)):
        raise ValueError("canonical_ids must be unique")
    by_engine: dict[str, list[dict]] = {}
    for record in live_records:
        engine_id = record.get("engine_id")
        if engine_id not in canonical:
            raise ValueError(f"live record references non-canonical engine: {engine_id}")
        by_engine.setdefault(engine_id, []).append(record)
    rows = []
    for engine_id in canonical:
        records = by_engine.get(engine_id, [])
        if not records:
            rows.append({"engine_id": engine_id, "state": DEFAULT_STATE, "evidence_refs": (), "record_count": 0})
            continue
        priority = {
            "CONFIRMED_OPERATIONAL": 7,
            "LAB_GREEN": 6,
            "HUMAN_REQUIRED": 5,
            "BLOCKED": 4,
            "DOCUMENTED_PARTIAL": 3,
            "DEFINED_NOT_BUILT": 2,
            "UNKNOWN_REQUIRES_AUDIT": 1,
        }
        selected = max(records, key=lambda item: priority.get(item.get("state"), 0))
        rows.append({
            "engine_id": engine_id,
            "state": selected.get("state", DEFAULT_STATE),
            "evidence_refs": tuple(selected.get("evidence_refs", ())),
            "record_count": len(records),
        })
    return tuple(rows)


def summarize(matrix: tuple[dict, ...] | list[dict]) -> dict:
    counts: dict[str, int] = {}
    for row in matrix:
        state = row["state"]
        counts[state] = counts.get(state, 0) + 1
    return {"total": len(matrix), "counts": dict(sorted(counts.items()))}

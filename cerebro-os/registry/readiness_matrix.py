from __future__ import annotations

DEFAULT_STATE = "UNKNOWN_REQUIRES_AUDIT"

# Conservative aggregation: an unresolved exception/blocker must never be hidden by
# a LAB green record from another scope/environment. CONFIRMED_OPERATIONAL is only
# selected ahead of non-blocking lower evidence states.
STATE_PRIORITY = {
    "HUMAN_REQUIRED": 9,
    "BLOCKED": 8,
    "CONFIRMED_OPERATIONAL": 7,
    "LAB_GREEN": 6,
    "DOCUMENTED_PARTIAL": 3,
    "DEFINED_NOT_BUILT": 2,
    "UNKNOWN_REQUIRES_AUDIT": 1,
}


def build_readiness_matrix(
    *,
    canonical_ids,
    live_records: list[dict] | tuple[dict, ...],
    company_id: str | None = None,
    environment: str | None = None,
) -> tuple[dict, ...]:
    """Build a conservative readiness view.

    A caller may scope the matrix by company/environment. Without an explicit
    scope the function intentionally gives unresolved HUMAN_REQUIRED/BLOCKED
    records precedence so a LAB_GREEN record cannot mask a real-environment gap.
    """
    canonical = tuple(canonical_ids)
    if len(canonical) != len(set(canonical)):
        raise ValueError("canonical_ids must be unique")
    if environment is not None and environment not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment filter")

    by_engine: dict[str, list[dict]] = {}
    for record in live_records:
        engine_id = record.get("engine_id")
        if engine_id not in canonical:
            raise ValueError(f"live record references non-canonical engine: {engine_id}")
        if company_id is not None and record.get("company_id") != company_id:
            continue
        if environment is not None and record.get("environment") != environment:
            continue
        by_engine.setdefault(engine_id, []).append(record)

    rows = []
    for engine_id in canonical:
        records = by_engine.get(engine_id, [])
        if not records:
            rows.append({
                "engine_id": engine_id,
                "state": DEFAULT_STATE,
                "evidence_refs": (),
                "record_count": 0,
                "company_id": company_id,
                "environment": environment,
            })
            continue
        selected = max(records, key=lambda item: STATE_PRIORITY.get(item.get("state"), 0))
        rows.append({
            "engine_id": engine_id,
            "state": selected.get("state", DEFAULT_STATE),
            "evidence_refs": tuple(selected.get("evidence_refs", ())),
            "record_count": len(records),
            "company_id": company_id,
            "environment": environment,
        })
    return tuple(rows)


def summarize(matrix: tuple[dict, ...] | list[dict]) -> dict:
    counts: dict[str, int] = {}
    for row in matrix:
        state = row["state"]
        counts[state] = counts.get(state, 0) + 1
    return {"total": len(matrix), "counts": dict(sorted(counts.items()))}

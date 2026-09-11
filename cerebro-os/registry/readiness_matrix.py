from __future__ import annotations

DEFAULT_STATE = "UNKNOWN_REQUIRES_AUDIT"

STATE_PRIORITY = {
    "HUMAN_REQUIRED": 9,
    "BLOCKED": 8,
    "CONFIRMED_OPERATIONAL": 7,
    "LAB_GREEN": 6,
    "DOCUMENTED_PARTIAL": 3,
    "DEFINED_NOT_BUILT": 2,
    "UNKNOWN_REQUIRES_AUDIT": 1,
}
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


def build_readiness_matrix(
    *,
    canonical_ids,
    live_records: list[dict] | tuple[dict, ...],
    company_id: str | None = None,
    environment: str | None = None,
    version: str | None = None,
) -> tuple[dict, ...]:
    """Build a conservative readiness view for an optional exact scope.

    When company/environment/version are supplied, records from any other scope
    are excluded. Without explicit filters unresolved blockers retain precedence.
    """
    canonical = tuple(canonical_ids)
    if len(canonical) != len(set(canonical)):
        raise ValueError("canonical_ids must be unique")
    if environment is not None and environment not in VALID_ENVIRONMENTS:
        raise ValueError("invalid environment filter")
    if version is not None and not version.strip():
        raise ValueError("version filter must be non-empty")

    by_engine: dict[str, list[dict]] = {}
    for record in live_records:
        engine_id = record.get("engine_id")
        if engine_id not in canonical:
            raise ValueError(f"live record references non-canonical engine: {engine_id}")
        if company_id is not None and record.get("company_id") != company_id:
            continue
        if environment is not None and record.get("environment") != environment:
            continue
        if version is not None and record.get("version") != version:
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
                "version": version,
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
            "version": version,
        })
    return tuple(rows)


def summarize(matrix: tuple[dict, ...] | list[dict]) -> dict:
    counts: dict[str, int] = {}
    for row in matrix:
        state = row["state"]
        counts[state] = counts.get(state, 0) + 1
    return {"total": len(matrix), "counts": dict(sorted(counts.items()))}

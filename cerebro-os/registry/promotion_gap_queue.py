from __future__ import annotations

REQUIRED_GATES = (
    "contracts",
    "permissions",
    "tests",
    "evaluation",
    "tribunal",
    "observability",
    "rollback",
    "backup",
    "rebuild",
    "cost",
    "policy",
    "tenant_isolation",
)

VALID_TARGETS = {"PREPROD", "PROD"}


def build_promotion_gap_queue(
    *,
    canonical_ids,
    company_id: str,
    target_environment: str,
    evidence_by_engine: dict[str, dict[str, str]],
) -> tuple[dict, ...]:
    """Return a fail-closed evidence queue; never mutates live engine state.

    An engine leaves this queue only after every mandatory promotion gate has a
    non-empty evidence reference. Being absent from the queue means READY_FOR_GATE,
    not automatically promoted or operational.
    """
    canonical = tuple(canonical_ids)
    if len(canonical) != len(set(canonical)):
        raise ValueError("canonical_ids must be unique")
    if not company_id.strip():
        raise ValueError("company_id required")
    if target_environment not in VALID_TARGETS:
        raise ValueError("target_environment must be PREPROD or PROD")
    unknown = set(evidence_by_engine) - set(canonical)
    if unknown:
        raise ValueError(f"evidence references non-canonical engines: {sorted(unknown)}")

    rows = []
    for position, engine_id in enumerate(canonical):
        refs = evidence_by_engine.get(engine_id, {})
        missing = tuple(gate for gate in REQUIRED_GATES if not str(refs.get(gate, "")).strip())
        if not missing:
            continue
        rows.append({
            "engine_id": engine_id,
            "company_id": company_id,
            "target_environment": target_environment,
            "missing_gates": missing,
            "missing_count": len(missing),
            "canonical_position": position,
            "state": "PROMOTION_EVIDENCE_GAP",
        })
    return tuple(sorted(rows, key=lambda row: (row["missing_count"], row["canonical_position"])))


def ready_for_gate(
    *,
    canonical_ids,
    company_id: str,
    target_environment: str,
    evidence_by_engine: dict[str, dict[str, str]],
) -> tuple[str, ...]:
    queue = build_promotion_gap_queue(
        canonical_ids=canonical_ids,
        company_id=company_id,
        target_environment=target_environment,
        evidence_by_engine=evidence_by_engine,
    )
    blocked = {row["engine_id"] for row in queue}
    return tuple(engine_id for engine_id in canonical_ids if engine_id not in blocked)

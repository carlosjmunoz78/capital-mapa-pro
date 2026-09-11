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
SCOPE_KEYS = ("company_id", "environment", "version")


def build_promotion_gap_queue(
    *,
    canonical_ids,
    company_id: str,
    target_environment: str,
    target_version: str,
    evidence_by_engine: dict[str, dict[str, str]],
) -> tuple[dict, ...]:
    """Return a fail-closed exact-scope evidence queue; never mutates live state.

    Evidence must explicitly match company, target environment and version. Plain
    gate booleans/refs from another scope can never remove an engine from the queue.
    """
    canonical = tuple(canonical_ids)
    if len(canonical) != len(set(canonical)):
        raise ValueError("canonical_ids must be unique")
    if not company_id.strip() or not target_version.strip():
        raise ValueError("company_id and target_version required")
    if target_environment not in VALID_TARGETS:
        raise ValueError("target_environment must be PREPROD or PROD")
    unknown = set(evidence_by_engine) - set(canonical)
    if unknown:
        raise ValueError(f"evidence references non-canonical engines: {sorted(unknown)}")

    rows = []
    for position, engine_id in enumerate(canonical):
        refs = evidence_by_engine.get(engine_id, {})
        scope_matches = (
            refs.get("company_id") == company_id
            and refs.get("environment") == target_environment
            and refs.get("version") == target_version
        )
        missing = tuple(gate for gate in REQUIRED_GATES if not str(refs.get(gate, "")).strip())
        if scope_matches and not missing:
            continue
        rows.append({
            "engine_id": engine_id,
            "company_id": company_id,
            "target_environment": target_environment,
            "target_version": target_version,
            "missing_gates": missing,
            "missing_count": len(missing),
            "scope_match": scope_matches,
            "state": "PROMOTION_EVIDENCE_GAP" if scope_matches else "PROMOTION_SCOPE_MISMATCH",
            "canonical_position": position,
        })
    return tuple(sorted(rows, key=lambda row: (0 if not row["scope_match"] else 1, row["missing_count"], row["canonical_position"])))


def ready_for_gate(
    *,
    canonical_ids,
    company_id: str,
    target_environment: str,
    target_version: str,
    evidence_by_engine: dict[str, dict[str, str]],
) -> tuple[str, ...]:
    queue = build_promotion_gap_queue(
        canonical_ids=canonical_ids,
        company_id=company_id,
        target_environment=target_environment,
        target_version=target_version,
        evidence_by_engine=evidence_by_engine,
    )
    blocked = {row["engine_id"] for row in queue}
    return tuple(engine_id for engine_id in canonical_ids if engine_id not in blocked)

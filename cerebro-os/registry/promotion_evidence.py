from __future__ import annotations

REQUIRED_KINDS = (
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
VALID_ENVIRONMENTS = {"PREPROD", "PROD"}


def collect_promotion_evidence(
    *,
    evidence_store,
    company_id: str,
    engine_id: str,
    version: str,
    environment: str,
) -> dict:
    """Collect exact-scope evidence refs for a real-environment promotion gate.

    Evidence from another tenant, engine, version or environment cannot satisfy
    this gate. Multiple records of one kind are preserved for audit; the most
    recent exact-scope reference is exposed as the gate ref.
    """
    if not all(isinstance(value, str) and value.strip() for value in (company_id, engine_id, version)):
        raise ValueError("company_id, engine_id and version required")
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError("promotion evidence is only collected for PREPROD/PROD")

    records = evidence_store.list_engine(company_id=company_id, engine_id=engine_id, environment=environment)
    by_kind: dict[str, list[dict]] = {kind: [] for kind in REQUIRED_KINDS}
    ignored = []
    for record in records:
        if record.get("version") != version:
            ignored.append(record.get("evidence_id"))
            continue
        kind = record.get("kind")
        if kind not in by_kind:
            ignored.append(record.get("evidence_id"))
            continue
        reference = str(record.get("reference", "")).strip()
        if not reference:
            ignored.append(record.get("evidence_id"))
            continue
        by_kind[kind].append(record)

    refs = {
        kind: rows[-1]["reference"]
        for kind, rows in by_kind.items()
        if rows
    }
    missing = tuple(kind for kind in REQUIRED_KINDS if kind not in refs)
    return {
        "company_id": company_id,
        "engine_id": engine_id,
        "version": version,
        "environment": environment,
        "ready": not missing,
        "refs": refs,
        "missing": missing,
        "ignored_evidence_ids": tuple(item for item in ignored if item),
        "record_counts": {kind: len(rows) for kind, rows in by_kind.items()},
    }

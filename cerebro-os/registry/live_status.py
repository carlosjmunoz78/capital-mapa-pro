from __future__ import annotations

VALID_STATES = {
    "CONFIRMED_OPERATIONAL",
    "LAB_GREEN",
    "DOCUMENTED_PARTIAL",
    "DEFINED_NOT_BUILT",
    "UNKNOWN_REQUIRES_AUDIT",
    "BLOCKED",
    "HUMAN_REQUIRED",
}

EVIDENCE_REQUIRED = {"CONFIRMED_OPERATIONAL", "LAB_GREEN"}
REAL_ENVIRONMENTS = {"PREPROD", "PROD"}


def _clean_refs(values) -> tuple[str, ...]:
    return tuple(ref.strip() for ref in values if isinstance(ref, str) and ref.strip())


def validate_live_status(record: dict) -> None:
    required = ("engine_id", "company_id", "environment", "version", "state")
    missing = tuple(key for key in required if not record.get(key))
    if missing:
        raise ValueError(f"missing status fields: {missing}")
    if record["state"] not in VALID_STATES:
        raise ValueError(f"invalid live state: {record['state']}")
    if record["environment"] not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment")

    refs = _clean_refs(record.get("evidence_refs", ()))
    if record["state"] in EVIDENCE_REQUIRED and not refs:
        raise ValueError("green/operational state requires non-empty evidence_refs")

    # Real-environment operational claims must be traceable to the promotion gate,
    # not merely to an arbitrary test/doc reference.
    if record["state"] == "CONFIRMED_OPERATIONAL" and record["environment"] in REAL_ENVIRONMENTS:
        promotion_gate_ref = str(record.get("promotion_gate_ref", "")).strip()
        if not promotion_gate_ref:
            raise ValueError("real-environment CONFIRMED_OPERATIONAL requires promotion_gate_ref")


def make_status(*, engine_id: str, company_id: str, environment: str, version: str, state: str, evidence_refs=(), notes: str = "", promotion_gate_ref: str = "") -> dict:
    record = {
        "engine_id": engine_id,
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "state": state,
        "evidence_refs": _clean_refs(evidence_refs),
        "notes": notes,
        "promotion_gate_ref": promotion_gate_ref.strip(),
    }
    validate_live_status(record)
    return record

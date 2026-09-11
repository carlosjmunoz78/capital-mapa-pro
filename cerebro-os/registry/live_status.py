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


def validate_live_status(record: dict) -> None:
    required = ("engine_id", "company_id", "environment", "version", "state")
    missing = tuple(key for key in required if not record.get(key))
    if missing:
        raise ValueError(f"missing status fields: {missing}")
    if record["state"] not in VALID_STATES:
        raise ValueError(f"invalid live state: {record['state']}")
    if record["state"] in EVIDENCE_REQUIRED and not record.get("evidence_refs"):
        raise ValueError("green/operational state requires evidence_refs")
    if record["environment"] not in {"LAB", "PREPROD", "PROD"}:
        raise ValueError("invalid environment")


def make_status(*, engine_id: str, company_id: str, environment: str, version: str, state: str, evidence_refs=(), notes: str = "") -> dict:
    record = {
        "engine_id": engine_id,
        "company_id": company_id,
        "environment": environment,
        "version": version,
        "state": state,
        "evidence_refs": tuple(evidence_refs),
        "notes": notes,
    }
    validate_live_status(record)
    return record

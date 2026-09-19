from __future__ import annotations

from dataclasses import dataclass

from observability.improvement_audit_store import ImprovementAuditStore

EXPECTED_STAGES = (
    "OBSERVE", "MEASURE", "DETECT", "PROPOSE", "LAB", "TEST",
    "EVALUATE", "TRIBUNAL", "OLD_VS_NEW", "CANARY",
    "PROMOTE_OR_ROLLBACK", "LEARN",
)


@dataclass(frozen=True)
class ImprovementCycleSummary:
    company_id: str
    environment: str
    cycle_id: str
    status: str
    stage_count: int
    total_cost_eur: float
    old_ref: str | None
    new_ref: str | None
    rollback_ref: str | None
    chain_verified: bool


def summarize_cycle(store: ImprovementAuditStore, *, company_id: str, environment: str, cycle_id: str) -> ImprovementCycleSummary:
    records = store.cycle_records(company_id=company_id, environment=environment, cycle_id=cycle_id)
    chain_verified = store.verify_chain(company_id=company_id, environment=environment)
    if not chain_verified:
        status = "TAMPERED"
    elif not records:
        status = "NO_DATA"
    else:
        statuses = [r["status"] for r in records]
        if "HUMAN_REQUIRED" in statuses:
            status = "HUMAN_REQUIRED"
        elif "BLOCKED" in statuses:
            status = "BLOCKED"
        elif "WAITING" in statuses:
            status = "WAITING"
        elif len(records) == len(EXPECTED_STAGES) and all(r["stage"] == EXPECTED_STAGES[i] and r["status"] == "GREEN" for i, r in enumerate(records)):
            status = "GREEN"
        elif any(s == "RED" for s in statuses):
            status = "RED"
        else:
            status = "IN_PROGRESS"

    total_cost = round(sum(float(r.get("cost_eur", 0.0)) for r in records), 6)
    old_ref = next((r.get("old_ref") for r in records if r.get("old_ref")), None)
    new_ref = next((r.get("new_ref") for r in records if r.get("new_ref")), None)
    rollback_ref = next((r.get("rollback_ref") for r in records if r.get("rollback_ref")), None)
    return ImprovementCycleSummary(
        company_id, environment, cycle_id, status, len(records), total_cost,
        old_ref, new_ref, rollback_ref, chain_verified,
    )


def supervisor_status(summary: ImprovementCycleSummary) -> dict:
    if summary.status == "TAMPERED":
        return {"status": "HUMAN_REQUIRED", "reason": "SECURITY_INCIDENT"}
    if summary.status in {"HUMAN_REQUIRED", "BLOCKED", "WAITING", "RED"}:
        return {"status": summary.status, "reason": None}
    if summary.status == "GREEN":
        complete_refs = bool(summary.old_ref and summary.new_ref and summary.rollback_ref)
        if not complete_refs:
            return {"status": "BLOCKED", "reason": "MISSING_PROMOTION_EVIDENCE"}
        return {"status": "GREEN", "reason": None}
    return {"status": summary.status, "reason": None}

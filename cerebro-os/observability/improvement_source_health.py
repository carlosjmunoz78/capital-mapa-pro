from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompanySourceHealth:
    company_id: str
    status: str
    required_failures: tuple[str, ...]
    optional_failures: tuple[str, ...]
    source_status: tuple[tuple[str, str], ...]
    evidence_ref: str


def read_company_source_health(evidence_root: Path, company_id: str) -> CompanySourceHealth:
    path = Path(evidence_root) / f"{company_id}.observations.json"
    if not path.exists():
        return CompanySourceHealth(
            company_id=company_id,
            status="NO_EVIDENCE",
            required_failures=("aggregate_missing",),
            optional_failures=(),
            source_status=(),
            evidence_ref=f"evidence://{company_id}/aggregate-missing",
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if str(payload.get("company_id", "")) != company_id:
        raise ValueError("cross-company aggregate evidence denied")
    facts = payload.get("facts") or {}
    missing_required = tuple(str(x) for x in facts.get("missing_required_sources", []))
    failed_required = tuple(str(x) for x in facts.get("failed_required_sources", []))
    optional_failures = tuple(str(x) for x in facts.get("failed_optional_sources", []))
    source_map = facts.get("source_status") or {}
    source_status = tuple(sorted(
        (str(name), str((detail or {}).get("status", "UNKNOWN")))
        for name, detail in source_map.items()
    ))
    required_failures = tuple(dict.fromkeys(missing_required + failed_required))
    aggregate_status = str(payload.get("status", "UNKNOWN"))
    if required_failures:
        status = "WAITING"
    elif aggregate_status == "HUMAN_REQUIRED":
        status = "HUMAN_REQUIRED"
    elif aggregate_status == "PROPOSAL_READY":
        status = "PROPOSAL_READY"
    elif aggregate_status == "NO_CHANGE":
        status = "GREEN"
    elif aggregate_status == "SOURCE_ERROR":
        status = "WAITING"
    else:
        status = aggregate_status
    return CompanySourceHealth(
        company_id=company_id,
        status=status,
        required_failures=required_failures,
        optional_failures=optional_failures,
        source_status=source_status,
        evidence_ref=str(payload.get("evidence_ref", "")),
    )


def fleet_source_health(evidence_root: Path, company_ids: tuple[str, ...]) -> dict:
    items = tuple(read_company_source_health(evidence_root, company_id) for company_id in company_ids)
    attention = tuple(
        item.company_id for item in items
        if item.status in {"WAITING", "HUMAN_REQUIRED", "PROPOSAL_READY", "NO_EVIDENCE"}
    )
    if any(item.status == "HUMAN_REQUIRED" for item in items):
        status = "HUMAN_REQUIRED"
    elif any(item.status in {"WAITING", "NO_EVIDENCE"} for item in items):
        status = "WAITING"
    elif any(item.status == "PROPOSAL_READY" for item in items):
        status = "PROPOSAL_READY"
    else:
        status = "GREEN"
    return {
        "status": status,
        "companies": tuple({
            "company_id": item.company_id,
            "status": item.status,
            "required_failures": item.required_failures,
            "optional_failures": item.optional_failures,
            "source_status": dict(item.source_status),
            "evidence_ref": item.evidence_ref,
        } for item in items),
        "attention_company_ids": attention,
    }

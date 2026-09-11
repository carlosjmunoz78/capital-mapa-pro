from __future__ import annotations

from typing import Iterable


def verified_lab_records(*, commit_sha: str, ci_run_id: str) -> tuple[dict, ...]:
    if not commit_sha.strip() or not ci_run_id.strip():
        raise ValueError("commit_sha and ci_run_id are required")
    common = (f"git:{commit_sha}", f"ci:{ci_run_id}")
    return (
        {
            "engine_id": "FACT-001",
            "company_id": "GLOBAL",
            "environment": "LAB",
            "version": commit_sha,
            "state": "LAB_GREEN",
            "evidence_refs": common + ("test:smoke_scaffold",),
            "notes": "Factory scaffold smoke test and full unit suite green.",
        },
        {
            "engine_id": "COH-001",
            "company_id": "GLOBAL",
            "environment": "LAB",
            "version": commit_sha,
            "state": "LAB_GREEN",
            "evidence_refs": common + ("test:test_loops_38_40:COH-001",),
            "notes": "Deterministic contradiction graph tested for tenant isolation, contradiction detection and low confidence escalation.",
        },
        {
            "engine_id": "VIA-001",
            "company_id": "GLOBAL",
            "environment": "LAB",
            "version": commit_sha,
            "state": "LAB_GREEN",
            "evidence_refs": common + ("test:test_loops_38_40:VIA-001",),
            "notes": "Versioned deterministic viability rule evaluator tested; no underwriting thresholds embedded in code.",
        },
    )


def overlay_live_inventory(canonical_ids: Iterable[str], verified_records: Iterable[dict]) -> tuple[dict, ...]:
    canonical = tuple(canonical_ids)
    record_map = {r["engine_id"]: dict(r) for r in verified_records}
    unknown = set(record_map) - set(canonical)
    if unknown:
        raise ValueError(f"verified records contain non-canonical ids: {sorted(unknown)}")
    rows: list[dict] = []
    for engine_id in canonical:
        if engine_id in record_map:
            rows.append(record_map[engine_id])
        else:
            rows.append({
                "engine_id": engine_id,
                "company_id": "GLOBAL",
                "environment": "LAB",
                "version": "UNVERIFIED",
                "state": "UNKNOWN_REQUIRES_AUDIT",
                "evidence_refs": (),
                "notes": "Logical controller coverage does not prove live engine readiness.",
            })
    return tuple(rows)

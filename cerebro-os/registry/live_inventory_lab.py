from __future__ import annotations

from typing import Iterable


VERIFIED_LAB_ENGINES = (
    "CORE-001", "GOV-001", "ORCH-001", "POL-001", "HEX-001", "DEC-001", "SEM-001",
    "OWN-001", "OBJ-001", "ADR-001", "CFG-001", "VER-001", "FACT-001", "COH-001", "VIA-001",
)


def _record(engine_id: str, commit_sha: str, ci_run_id: str, test_ref: str, notes: str) -> dict:
    return {
        "engine_id": engine_id,
        "company_id": "GLOBAL",
        "environment": "LAB",
        "version": commit_sha,
        "state": "LAB_GREEN",
        "evidence_refs": (f"git:{commit_sha}", f"ci:{ci_run_id}", test_ref),
        "notes": notes,
    }


def verified_lab_records(*, commit_sha: str, ci_run_id: str) -> tuple[dict, ...]:
    if not commit_sha.strip() or not ci_run_id.strip():
        raise ValueError("commit_sha and ci_run_id are required")
    records = [
        _record("CORE-001", commit_sha, ci_run_id, "test:test_loops_41_50:CORE-001", "Company-scoped, versioned, provenanced core state."),
        _record("GOV-001", commit_sha, ci_run_id, "test:test_governance:registry", "Registry validation and canonical registry checks green."),
        _record("ORCH-001", commit_sha, ci_run_id, "test:test_loops_41_50:ORCH-001", "Dependency-aware priority orchestration and retries tested."),
        _record("POL-001", commit_sha, ci_run_id, "test:test_governance:policy", "Deterministic policy, cross-company deny and human exceptions tested."),
        _record("HEX-001", commit_sha, ci_run_id, "test:test_loops_41_50:HEX-001", "Canonical human exception queue tested."),
        _record("DEC-001", commit_sha, ci_run_id, "test:test_loops_41_50:DEC-001", "Deterministic explainable decision scoring tested."),
        _record("SEM-001", commit_sha, ci_run_id, "test:test_loops_41_50:SEM-001", "Semantic catalog and duplicate protection tested."),
        _record("OWN-001", commit_sha, ci_run_id, "test:test_loops_41_50:OWN-001", "Owner, approver and backup ownership contract tested."),
        _record("OBJ-001", commit_sha, ci_run_id, "test:test_loops_41_50:OBJ-001", "Objective metric evaluation tested."),
        _record("ADR-001", commit_sha, ci_run_id, "test:test_loops_41_50:ADR-001", "Append-only architecture decision records with rollback tested."),
        _record("CFG-001", commit_sha, ci_run_id, "test:test_loops_41_50:CFG-001", "Environment configuration and secret rejection tested."),
        _record("VER-001", commit_sha, ci_run_id, "test:test_loops_41_50:VER-001", "Semver and breaking-major compatibility gate tested."),
        _record("FACT-001", commit_sha, ci_run_id, "test:smoke_scaffold", "Factory scaffold smoke test and full unit suite green."),
        _record("COH-001", commit_sha, ci_run_id, "test:test_loops_38_40:COH-001", "Deterministic contradiction graph, tenant isolation and low-confidence escalation tested."),
        _record("VIA-001", commit_sha, ci_run_id, "test:test_loops_38_40:VIA-001", "Versioned deterministic viability rules, confidence and explanations tested; no underwriting thresholds embedded."),
    ]
    if tuple(r["engine_id"] for r in records) != VERIFIED_LAB_ENGINES:
        raise AssertionError("verified lab engine catalog drift")
    return tuple(records)


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

from __future__ import annotations

from typing import Iterable


VERIFIED_LAB_ENGINES = (
    # L0: dedicated deterministic implementations/tests
    "CORE-001", "GOV-001", "ORCH-001", "POL-001", "HEX-001", "DEC-001", "SEM-001",
    "OWN-001", "OBJ-001", "ADR-001", "CFG-001", "VER-001", "FACT-001",
    # L1: knowledge, learning, training, evaluation, research and retrieval
    "KNW-001", "PRV-001", "LRN-001", "TRN-001", "EVA-001", "JDG-001", "RSH-001",
    "UPD-001", "OBS-001", "RAG-001", "CON-001", "CACHE-001",
    # L2/shared control pieces with dedicated tests
    "SUP-001", "OBSERV-001",
    # Mortgage engines closed with dedicated logic
    "COH-001", "VIA-001",
    # Shared runtime/platform pieces with dedicated tests
    "FINOPS-001", "EVT-001", "JOB-001", "AUD-001", "RUNTIME-001", "TENANT-001",
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
    refs = {
        "CORE-001": ("test:test_loops_41_50:CORE-001", "Company-scoped, versioned, provenanced core state."),
        "GOV-001": ("test:test_governance:registry", "Registry validation and canonical registry checks green."),
        "ORCH-001": ("test:test_loops_41_50:ORCH-001", "Dependency-aware priority orchestration and retries tested."),
        "POL-001": ("test:test_governance:policy", "Deterministic policy, cross-company deny and human exceptions tested."),
        "HEX-001": ("test:test_loops_41_50:HEX-001", "Canonical human exception queue tested."),
        "DEC-001": ("test:test_loops_41_50:DEC-001", "Deterministic explainable decision scoring tested."),
        "SEM-001": ("test:test_loops_41_50:SEM-001", "Semantic catalog and duplicate protection tested."),
        "OWN-001": ("test:test_loops_41_50:OWN-001", "Owner, approver and backup ownership contract tested."),
        "OBJ-001": ("test:test_loops_41_50:OBJ-001", "Objective metric evaluation tested."),
        "ADR-001": ("test:test_loops_41_50:ADR-001", "Append-only architecture decisions with rollback tested."),
        "CFG-001": ("test:test_loops_41_50:CFG-001", "Environment config and secret rejection tested."),
        "VER-001": ("test:test_loops_41_50:VER-001", "Semver and breaking-major compatibility gate tested."),
        "FACT-001": ("test:smoke_scaffold", "Factory scaffold smoke test and full unit suite green."),
        "KNW-001": ("test:test_loops_knowledge_cost_bootstrap:knowledge", "Tenant-scoped knowledge index with provenance tested."),
        "PRV-001": ("test:test_loops_knowledge_cost_bootstrap:provenance", "Knowledge provenance is mandatory and tested."),
        "LRN-001": ("test:test_loops_51_54:LRN-001", "Outcome learning produces review-only rule candidates."),
        "TRN-001": ("test:test_loops_51_54:TRN-001", "Versioned/reproducible training and tribunal-gated champion promotion tested."),
        "EVA-001": ("test:test_quality_observability:evaluation", "Evaluation requires evidence and threshold pass."),
        "JDG-001": ("test:test_quality_observability:tribunal", "Tribunal requires all canonical gates."),
        "RSH-001": ("test:test_loops_51_54:RSH-001", "Research dossier preserves sources and cannot write current knowledge directly."),
        "UPD-001": ("test:test_loops_19_21:update", "Knowledge updates invalidate cache and preserve versions."),
        "OBS-001": ("test:test_loops_19_21:freshness", "Knowledge staleness/freshness detection tested."),
        "RAG-001": ("test:test_loops_19_21:retrieval", "Tenant-scoped deterministic retrieval tested."),
        "CON-001": ("test:test_loops_51_54:CON-001", "Structured conversation extraction and confidence escalation tested."),
        "CACHE-001": ("test:test_loops_19_21:cache", "Query cache and update invalidation tested."),
        "SUP-001": ("test:test_quality_observability:supervisor", "Supervisor requires all health gates green and respects HUMAN_REQUIRED."),
        "OBSERV-001": ("test:test_quality_observability:observability", "Execution record validation includes evidence, duration and cost."),
        "COH-001": ("test:test_loops_38_40:COH-001", "Contradiction graph, tenant isolation and confidence escalation tested."),
        "VIA-001": ("test:test_loops_38_40:VIA-001", "Versioned viability rules, confidence and explanations tested; no thresholds embedded."),
        "FINOPS-001": ("test:test_tenant_finops:finops", "Zero-cost default and MONEY_LIMIT enforcement tested."),
        "EVT-001": ("test:test_runtime:event", "Multi-company event envelope and persistent tenant-scoped runtime tested."),
        "JOB-001": ("test:test_runtime:jobs", "Idempotent job queue and retry limit tested."),
        "AUD-001": ("test:test_runtime:audit", "Audit contract includes policy result and cost."),
        "RUNTIME-001": ("test:test_loop_registry_runtime_gateway:sqlite_runtime", "SQLite shared runtime persistence is tenant-scoped and idempotent."),
        "TENANT-001": ("test:test_tenant_finops:tenant", "Missing/cross-company access denied; same-company allowed."),
    }
    records = [_record(engine_id, commit_sha, ci_run_id, *refs[engine_id]) for engine_id in VERIFIED_LAB_ENGINES]
    return tuple(records)


def overlay_live_inventory(canonical_ids: Iterable[str], verified_records: Iterable[dict]) -> tuple[dict, ...]:
    canonical = tuple(canonical_ids)
    record_map = {r["engine_id"]: dict(r) for r in verified_records}
    if len(record_map) != len(tuple(verified_records)):
        raise ValueError("duplicate verified engine record")
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

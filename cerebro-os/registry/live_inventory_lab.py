from __future__ import annotations

from typing import Iterable


# Only engines with dedicated executable LAB behavior + tests belong here.
# Generic controller/scaffold coverage alone is intentionally excluded.
TEST_EVIDENCE = {
    # L0
    "CORE-001": "test:test_loops_41_50:CORE-001",
    "GOV-001": "test:test_governance:registry",
    "ORCH-001": "test:test_loops_41_50:ORCH-001",
    "POL-001": "test:test_governance:policy",
    "HEX-001": "test:test_loops_41_50:HEX-001",
    "DEC-001": "test:test_loops_41_50:DEC-001",
    "SEM-001": "test:test_loops_41_50:SEM-001",
    "OWN-001": "test:test_loops_41_50:OWN-001",
    "OBJ-001": "test:test_loops_41_50:OBJ-001",
    "ADR-001": "test:test_loops_41_50:ADR-001",
    "CFG-001": "test:test_loops_41_50:CFG-001",
    "VER-001": "test:test_loops_41_50:VER-001",
    "FACT-001": "test:smoke_scaffold",
    # L1
    "KNW-001": "test:test_loops_knowledge_cost_bootstrap:knowledge",
    "PRV-001": "test:test_loops_knowledge_cost_bootstrap:provenance",
    "LRN-001": "test:test_loops_51_54:LRN-001",
    "TRN-001": "test:test_loops_51_54:TRN-001",
    "EVA-001": "test:test_quality_observability:evaluation",
    "JDG-001": "test:test_quality_observability:tribunal",
    "RSH-001": "test:test_loops_51_54:RSH-001",
    "UPD-001": "test:test_loops_19_21:update",
    "OBS-001": "test:test_loops_19_21:freshness",
    "RAG-001": "test:test_loops_19_21:retrieval",
    "CON-001": "test:test_loops_51_54:CON-001",
    "CACHE-001": "test:test_loops_19_21:cache",
    # L2
    "SIM-001": "test:test_loops_55_67:SIM-001",
    "TWIN-001": "test:test_loops_55_67:TWIN-001",
    "SUP-001": "test:test_quality_observability:supervisor",
    "OBSERV-001": "test:test_quality_observability:observability",
    "INC-001": "test:test_loops_55_67:INC-001",
    "SELF-001": "test:test_loops_55_67:SELF-001",
    "SEC-001": "test:test_loops_55_67:SEC-001",
    "IAM-001": "test:test_loops_55_67:IAM-001",
    "SEC-002": "test:test_loops_55_67:SEC-002",
    "RED-001": "test:test_loops_55_67:RED-001",
    "QA-001": "test:test_loops_55_67:QA-001",
    "QAB-001": "test:test_loops_55_67:QAB-001",
    "REG-001": "test:test_loops_55_67:REG-001",
    "DR-001": "test:test_loop_registry_runtime_gateway:backup_restore",
    "RBLD-001": "test:test_loop_registry_runtime_gateway:rebuild",
    "BCP-001": "test:test_loops_55_67:BCP-001",
    "CRS-001": "test:test_loops_55_67:CRS-001",
    # L4 specific additions
    "COH-001": "test:test_loops_38_40:COH-001",
    "VIA-001": "test:test_loops_38_40:VIA-001",
    # Shared platform pieces with dedicated behavior
    "FINOPS-001": "test:test_tenant_finops:finops",
    "EVT-001": "test:test_runtime:event",
    "JOB-001": "test:test_runtime:jobs",
    "AUD-001": "test:test_runtime:audit",
    "RUNTIME-001": "test:test_loop_registry_runtime_gateway:sqlite_runtime",
    "TENANT-001": "test:test_tenant_finops:tenant",
}

VERIFIED_LAB_ENGINES = tuple(TEST_EVIDENCE)


def verified_lab_records(*, commit_sha: str, ci_run_id: str) -> tuple[dict, ...]:
    if not commit_sha.strip() or not ci_run_id.strip():
        raise ValueError("commit_sha and ci_run_id are required")
    return tuple(
        {
            "engine_id": engine_id,
            "company_id": "GLOBAL",
            "environment": "LAB",
            "version": commit_sha,
            "state": "LAB_GREEN",
            "evidence_refs": (f"git:{commit_sha}", f"ci:{ci_run_id}", test_ref),
            "notes": "Dedicated executable LAB behavior is covered by the referenced test; this does not assert PROD integration.",
        }
        for engine_id, test_ref in TEST_EVIDENCE.items()
    )


def overlay_live_inventory(canonical_ids: Iterable[str], verified_records: Iterable[dict]) -> tuple[dict, ...]:
    canonical = tuple(canonical_ids)
    records = tuple(verified_records)
    record_map = {r["engine_id"]: dict(r) for r in records}
    if len(record_map) != len(records):
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

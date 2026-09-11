from __future__ import annotations

from typing import Iterable


# Evidence-first LAB catalog. LAB_GREEN means the engine's dedicated contract/behavior
# has executable tests in this branch. It does NOT mean external integration or PROD readiness.
TEST_EVIDENCE: dict[str, str] = {
    # Foundation / knowledge / resilience / existing shared runtime.
    "CORE-001":"test:test_loops_41_50:CORE-001","GOV-001":"test:test_governance:registry","ORCH-001":"test:test_loops_41_50:ORCH-001","POL-001":"test:test_governance:policy","HEX-001":"test:test_loops_41_50:HEX-001","DEC-001":"test:test_loops_41_50:DEC-001","SEM-001":"test:test_loops_41_50:SEM-001","OWN-001":"test:test_loops_41_50:OWN-001","OBJ-001":"test:test_loops_41_50:OBJ-001","ADR-001":"test:test_loops_41_50:ADR-001","CFG-001":"test:test_loops_41_50:CFG-001","VER-001":"test:test_loops_41_50:VER-001","FACT-001":"test:smoke_scaffold",
    "KNW-001":"test:test_loops_knowledge_cost_bootstrap:knowledge","PRV-001":"test:test_loops_knowledge_cost_bootstrap:provenance","LRN-001":"test:test_loops_51_54:LRN-001","TRN-001":"test:test_loops_51_54:TRN-001","EVA-001":"test:test_quality_observability:evaluation","JDG-001":"test:test_quality_observability:tribunal","RSH-001":"test:test_loops_51_54:RSH-001","UPD-001":"test:test_loops_19_21:update","OBS-001":"test:test_loops_19_21:freshness","RAG-001":"test:test_loops_19_21:retrieval","CON-001":"test:test_loops_51_54:CON-001","CACHE-001":"test:test_loops_19_21:cache",
    "SIM-001":"test:test_loops_55_67:SIM-001","TWIN-001":"test:test_loops_55_67:TWIN-001","SUP-001":"test:test_quality_observability:supervisor","OBSERV-001":"test:test_quality_observability:observability","INC-001":"test:test_loops_55_67:INC-001","SELF-001":"test:test_loops_55_67:SELF-001","SEC-001":"test:test_loops_55_67:SEC-001","IAM-001":"test:test_loops_55_67:IAM-001","SEC-002":"test:test_loops_55_67:SEC-002","RED-001":"test:test_loops_55_67:RED-001","QA-001":"test:test_loops_55_67:QA-001","QAB-001":"test:test_loops_55_67:QAB-001","REG-001":"test:test_loops_55_67:REG-001","DR-001":"test:test_loop_registry_runtime_gateway:backup_restore","RBLD-001":"test:test_loop_registry_runtime_gateway:rebuild","BCP-001":"test:test_loops_55_67:BCP-001","CRS-001":"test:test_loops_55_67:CRS-001",
    "COH-001":"test:test_loops_38_40:COH-001","VIA-001":"test:test_loops_38_40:VIA-001",
    "FINOPS-001":"test:test_tenant_finops:finops","EVT-001":"test:test_runtime:event","JOB-001":"test:test_runtime:jobs","AUD-001":"test:test_runtime:audit","RUNTIME-001":"test:test_loop_registry_runtime_gateway:sqlite_runtime","TENANT-001":"test:test_tenant_finops:tenant",
}


def _batch(engine_ids: tuple[str, ...], test_file: str) -> None:
    for engine_id in engine_ids:
        if engine_id in TEST_EVIDENCE:
            raise AssertionError(f"duplicate evidence mapping: {engine_id}")
        TEST_EVIDENCE[engine_id] = f"test:{test_file}:{engine_id}"


# Commercial L3.
_batch(("MKT-001","SEO-001","CAP-001","LEAD-001","SALE-001","COM-001","NOTIF-001","VOICE-001","C360-001","CX-001","RET-001","POST-001","REF-001","REP-001","CMP-001","COMPET-001"), "test_loops_68_83")
# Mortgage/document L4 excluding COH/VIA already mapped above.
_batch(("DOC-001","DOC-002","DOC-003","DOC-004","KYC-001","AML-001","BNK-001","BNK-002","BNK-003","BNK-004","BNK-005","BNK-006","OFR-001","REC-001","TAS-001","PROP-001","REGP-001","CAT-001","NOT-001","PAY-001","SLA-001","BLK-001","NBA-001","AGD-001","3RD-001"), "test_loops_84_108")
# Enterprise L5 excluding FINOPS already mapped.
_batch(("HR-001","HR-002","HR-003","HR-004","HR-005","HR-006","LEG-001","TAX-001","CMP-002","DPO-001","CONS-001","INV-001","COL-001","TRE-001","ACC-001","VEN-001","BUY-001","VREP-001","VCON-001"), "test_loops_109_127")
# Technical platform L6 excluding EVT/JOB/AUD/RUNTIME already mapped.
_batch(("APP-001","CRM-001","DATA-001","API-001","DEP-001","ARCH-001","DEBT-001","MIG-001","FF-001","CAN-001","ROUTE-001","LOCAL-001","AIBUD-001","OPT-001","AUTO-001","DOCS-001","WEB-001","INT-001","DBOFF-001","STOROFF-001","FREE-001"), "test_loops_128_148")
# Strategy / labs / expansion.
_batch(("STR-001","FRC-001","CAPA-001","OPP-001","INN-001","EXP-001","LAB-TRD","LAB-SEO","LAB-MKT","LAB-AI","LAB-AUT","MKT-002","EXPAND-001","FRAN-001","VENT-001"), "test_loops_149_163")
# Multi-company onboarding/bootstrap, excluding TENANT already mapped.
_batch(("COMP-REG-001","COMP-ONB-001","SCAN-001","KW-001","WAUD-001","SOCAUD-001","LOCALP-001","BMD-001","PROC-001","KBOOT-001","SEOBOOT-001","SOCBOOT-001","MKTBOOT-001","CRMBOOT-001","APPBOOT-001","AUTBOOT-001","TRNBOOT-001","ENGACT-001","COMP-DEP-001","COMP-HLT-001","COMP-BKP-001","COMP-OFF-001"), "test_loops_164_185")
# Console / UI.
_batch(("CONSOLE-001","CHAT-001","CTX-001","CMD-001","ACTGW-001","DIRUI-001","TIMELINE-001","WHY-001","VOICEUI-001"), "test_loops_186_194")

VERIFIED_LAB_ENGINES = tuple(TEST_EVIDENCE)


def verified_lab_records(*, commit_sha: str, ci_run_id: str) -> tuple[dict, ...]:
    if not commit_sha.strip() or not ci_run_id.strip():
        raise ValueError("commit_sha and ci_run_id are required")
    return tuple({
        "engine_id": engine_id,
        "company_id": "GLOBAL",
        "environment": "LAB",
        "version": commit_sha,
        "state": "LAB_GREEN",
        "evidence_refs": (f"git:{commit_sha}", f"ci:{ci_run_id}", test_ref),
        "notes": "Dedicated executable LAB behavior is covered by tests; external integration and PROD readiness are separate gates.",
    } for engine_id, test_ref in TEST_EVIDENCE.items())


def overlay_live_inventory(canonical_ids: Iterable[str], verified_records: Iterable[dict]) -> tuple[dict, ...]:
    canonical = tuple(canonical_ids)
    records = tuple(verified_records)
    record_map = {r["engine_id"]: dict(r) for r in records}
    if len(record_map) != len(records):
        raise ValueError("duplicate verified engine record")
    unknown = set(record_map) - set(canonical)
    if unknown:
        raise ValueError(f"verified records contain non-canonical ids: {sorted(unknown)}")
    rows=[]
    for engine_id in canonical:
        rows.append(record_map.get(engine_id, {
            "engine_id":engine_id,"company_id":"GLOBAL","environment":"LAB","version":"UNVERIFIED",
            "state":"UNKNOWN_REQUIRES_AUDIT","evidence_refs":(),
            "notes":"Logical controller coverage does not prove live engine readiness.",
        }))
    return tuple(rows)

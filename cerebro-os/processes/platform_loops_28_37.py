from __future__ import annotations

LOOPS_28_37 = {
    "LOOP-28-CORE-GOVERNANCE": (
        "CORE-001", "GOV-001", "ORCH-001", "POL-001", "HEX-001", "DEC-001", "SEM-001",
        "OWN-001", "OBJ-001", "ADR-001", "CFG-001", "VER-001", "FACT-001",
    ),
    "LOOP-29-KNOWLEDGE-QUALITY": (
        "KNW-001", "PRV-001", "LRN-001", "TRN-001", "EVA-001", "JDG-001", "RSH-001",
        "UPD-001", "OBS-001", "RAG-001", "CON-001", "CACHE-001",
    ),
    "LOOP-30-SIMULATION-SUPERVISION": (
        "SIM-001", "TWIN-001", "SUP-001", "OBSERV-001", "INC-001", "SELF-001",
    ),
    "LOOP-31-SECURITY-RESILIENCE": (
        "SEC-001", "IAM-001", "SEC-002", "RED-001", "QA-001", "QAB-001", "REG-001",
        "DR-001", "RBLD-001", "BCP-001", "CRS-001",
    ),
    "LOOP-32-MARKET-COMMERCIAL-INTELLIGENCE": (
        "MKT-001", "SEO-001", "CAP-001", "CMP-001", "COMPET-001",
    ),
    "LOOP-33-APP-DATA-PLATFORM": (
        "APP-001", "CRM-001", "DATA-001", "EVT-001", "JOB-001", "API-001", "DEP-001",
        "ARCH-001", "DEBT-001", "MIG-001", "FF-001", "CAN-001",
    ),
    "LOOP-34-ROUTING-AUTOMATION-DOCS": (
        "ROUTE-001", "LOCAL-001", "AIBUD-001", "OPT-001", "AUTO-001", "DOCS-001", "AUD-001",
        "WEB-001", "INT-001", "RUNTIME-001", "DBOFF-001", "STOROFF-001", "FREE-001",
    ),
    "LOOP-35-LABS": (
        "LAB-TRD", "LAB-SEO", "LAB-MKT", "LAB-AI", "LAB-AUT",
    ),
    "LOOP-36-COMPANY-LIFECYCLE": (
        "COMP-REG-001", "COMP-ONB-001", "SCAN-001", "KW-001", "WAUD-001", "SOCAUD-001",
        "LOCALP-001", "BMD-001", "PROC-001", "KBOOT-001", "ENGACT-001", "TENANT-001",
        "COMP-DEP-001", "COMP-HLT-001", "COMP-BKP-001", "COMP-OFF-001",
    ),
    "LOOP-37-CONSOLE-UI": (
        "CONSOLE-001", "CHAT-001", "CTX-001", "CMD-001", "ACTGW-001", "DIRUI-001",
        "TIMELINE-001", "WHY-001", "VOICEUI-001",
    ),
}

LOOP_ORDER = tuple(LOOPS_28_37)
LAB_ONLY_ENGINES = frozenset({"LAB-TRD", "LAB-SEO", "LAB-MKT", "LAB-AI", "LAB-AUT"})


def all_engine_ids() -> tuple[str, ...]:
    return tuple(engine_id for sequence in LOOPS_28_37.values() for engine_id in sequence)


def validate_against_canonical(canonical: set[str]) -> None:
    if len(LOOPS_28_37) != 10:
        raise ValueError("exactly ten loops required")
    ids = all_engine_ids()
    unknown = sorted(set(ids) - canonical)
    if unknown:
        raise ValueError(f"non-canonical engine ids: {unknown}")
    if len(ids) != len(set(ids)):
        raise ValueError("engine ids must be unique across loops 28-37")

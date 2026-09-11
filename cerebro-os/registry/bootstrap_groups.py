from __future__ import annotations

BOOTSTRAP_GROUPS = (
    ("FACTORY_REGISTRY", ("FACT-001", "GOV-001")),
    ("SHARED_RUNTIME", ("RUNTIME-001", "EVT-001", "JOB-001", "API-001", "DATA-001")),
    ("CONTROL_PLANE", ("POL-001", "IAM-001", "SEC-001", "AUD-001", "QA-001", "EVA-001", "JDG-001", "OBSERV-001", "SUP-001", "FINOPS-001")),
    ("ZERO_COST_OFFLOAD", ("FREE-001", "DBOFF-001", "STOROFF-001", "LOCAL-001", "ROUTE-001", "AIBUD-001")),
    ("MULTICOMPANY", ("COMP-REG-001", "COMP-ONB-001", "TENANT-001", "COMP-DEP-001", "COMP-HLT-001", "COMP-BKP-001")),
    ("CONSOLE", ("CONSOLE-001", "CHAT-001", "CTX-001", "CMD-001", "ACTGW-001")),
)


def validate_bootstrap_groups(canonical_ids: tuple[str, ...] | list[str]) -> dict:
    canonical = set(canonical_ids)
    seen: set[str] = set()
    missing: list[str] = []
    duplicates: list[str] = []
    flattened: list[str] = []
    for _, engine_ids in BOOTSTRAP_GROUPS:
        for engine_id in engine_ids:
            flattened.append(engine_id)
            if engine_id not in canonical:
                missing.append(engine_id)
            if engine_id in seen:
                duplicates.append(engine_id)
            seen.add(engine_id)
    return {
        "valid": not missing and not duplicates,
        "missing": tuple(sorted(set(missing))),
        "duplicates": tuple(sorted(set(duplicates))),
        "engine_ids": tuple(flattened),
    }


def group_for(engine_id: str) -> str | None:
    for group, engine_ids in BOOTSTRAP_GROUPS:
        if engine_id in engine_ids:
            return group
    return None

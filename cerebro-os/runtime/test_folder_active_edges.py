from __future__ import annotations

ACTIVE_TEST_FOLDER_EDGES = {
    9538231: {
        "kind": "PROD_SEO_GA4_READ_ONLY",
        "folder_id": 520862,
        "preserve_active": True,
        "external_mutation": False,
    },
    9555725: {
        "kind": "CORE_SIGNAL_TO_LAB_TEST_PROTECTED",
        "folder_id": 520862,
        "preserve_active": True,
        "external_mutation": True,
    },
}


def assess_active_edge(scenario_id: int, *, connection_ok: bool, incomplete_executions: int) -> dict:
    if scenario_id not in ACTIVE_TEST_FOLDER_EDGES:
        raise ValueError("unknown active TEST-folder edge")
    if incomplete_executions < 0:
        raise ValueError("incomplete_executions must be non-negative")
    cfg = ACTIVE_TEST_FOLDER_EDGES[scenario_id]
    green = connection_ok and incomplete_executions == 0
    return {
        "scenario_id": scenario_id,
        "kind": cfg["kind"],
        "folder_id": cfg["folder_id"],
        "status": "PRESERVE_ACTIVE_EDGE_GREEN" if green else "ACTIVE_EDGE_BLOCKED",
        "preserve_active": cfg["preserve_active"],
        "external_mutation": cfg["external_mutation"],
        "runtime_duplicate_execution_allowed": False,
        "automatic_relocation_allowed": False,
        "delete_allowed": False,
    }


def inventory() -> set[int]:
    return set(ACTIVE_TEST_FOLDER_EDGES)

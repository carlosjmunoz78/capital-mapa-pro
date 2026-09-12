from __future__ import annotations

HEALTH_EXTERNAL_TARGETS = {
    9527663: ("facebook_oauth", "READ_ONLY"),
    9527908: ("facebook_pages_metrics", "READ_ONLY"),
    9522860: ("linkedin_health", "READ_ONLY"),
    9537666: ("youtube_health", "READ_ONLY"),
}

HEALTH_INTERNAL_TARGETS = {
    9527636: "alert_classification_dedup",
    9527843: "alert_queue_silencing",
    9527602: "core_deterministic_monitor",
    9527718: "facebook_capture_windows",
}


def assess_external_health(scenario_id: int, *, connection_ok: bool, incomplete_executions: int) -> dict:
    if scenario_id not in HEALTH_EXTERNAL_TARGETS:
        raise ValueError("unknown external health target")
    if incomplete_executions < 0:
        raise ValueError("incomplete_executions must be non-negative")
    green = connection_ok and incomplete_executions == 0
    return {
        "scenario_id": scenario_id,
        "kind": HEALTH_EXTERNAL_TARGETS[scenario_id][0],
        "mode": "READ_ONLY",
        "status": "HEALTH_EDGE_GREEN" if green else "HEALTH_EDGE_BLOCKED",
        "connection_ok": connection_ok,
        "incomplete_executions": incomplete_executions,
        "external_mutation_allowed": False,
        "publication_allowed": False,
        "notion_mutation_allowed": False,
        "auto_activate_allowed": False,
    }


def assess_internal_health(scenario_id: int, *, incomplete_executions: int) -> dict:
    if scenario_id not in HEALTH_INTERNAL_TARGETS:
        raise ValueError("unknown internal health target")
    if incomplete_executions < 0:
        raise ValueError("incomplete_executions must be non-negative")
    return {
        "scenario_id": scenario_id,
        "kind": HEALTH_INTERNAL_TARGETS[scenario_id],
        "status": "INTERNAL_MONITOR_GREEN" if incomplete_executions == 0 else "INTERNAL_MONITOR_BLOCKED",
        "external_mutation_allowed": False,
        "publication_allowed": False,
        "auto_activate_allowed": False,
    }


def inventory() -> set[int]:
    return set(HEALTH_EXTERNAL_TARGETS) | set(HEALTH_INTERNAL_TARGETS)

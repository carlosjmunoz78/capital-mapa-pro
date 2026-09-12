from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoreActiveEdge:
    scenario_id: int
    family: str
    disposition: str
    existing_active: bool
    incomplete_executions: int
    connector_health_ok: bool
    platform_publish_capable: bool
    writes_internal_state: bool


CORE_ACTIVE_EDGES = {
    9534096: CoreActiveEdge(9534096, "instagram_analytics", "KEEP_SAAS_CONNECTOR_EDGE", True, 0, True, False, True),
    9534088: CoreActiveEdge(9534088, "instagram_reconciliation", "KEEP_SAAS_CONNECTOR_EDGE", True, 0, True, False, True),
    9523007: CoreActiveEdge(9523007, "linkedin_analytics", "KEEP_SAAS_CONNECTOR_EDGE", True, 0, True, False, True),
    9405249: CoreActiveEdge(9405249, "linkedin_reconciliation", "KEEP_SAAS_CONNECTOR_EDGE", True, 0, True, False, True),
    9768402: CoreActiveEdge(9768402, "incoming_messaging", "KEEP_EXISTING_APP_EDGE_WRAP", True, 0, True, False, True),
    9527242: CoreActiveEdge(9527242, "universal_reconciliation", "MIGRATE_DETERMINISTIC_LOGIC_TO_RUNTIME", True, 0, True, False, True),
    9705138: CoreActiveEdge(9705138, "social_t72_t48_watchdog", "KEEP_EXISTING_NOTION_EDGE_WRAP", True, 0, True, False, True),
    9533690: CoreActiveEdge(9533690, "facebook_control_analytics", "KEEP_SAAS_CONNECTOR_EDGE", True, 0, True, False, True),
}


def assess_core_active_edge(scenario_id: int) -> dict:
    edge = CORE_ACTIVE_EDGES.get(int(scenario_id))
    if edge is None:
        return {
            "state": "UNKNOWN_EDGE",
            "human_required": True,
            "human_reason": "LOW_CONFIDENCE",
            "auto_disable_old": False,
            "auto_activate_replacement": False,
            "external_action_allowed": False,
        }

    blockers = []
    if not edge.existing_active:
        blockers.append("NOT_ACTIVE")
    if edge.incomplete_executions:
        blockers.append("INCOMPLETE_EXECUTIONS")
    if not edge.connector_health_ok:
        blockers.append("CONNECTOR_UNHEALTHY")
    if edge.platform_publish_capable:
        blockers.append("UNEXPECTED_PLATFORM_PUBLISH_CAPABILITY")

    return {
        "scenario_id": edge.scenario_id,
        "family": edge.family,
        "disposition": edge.disposition,
        "state": "PRESERVE_AND_WRAP" if not blockers else "BLOCKED",
        "blockers": tuple(blockers),
        "writes_internal_state": edge.writes_internal_state,
        "auto_disable_old": False,
        "auto_activate_replacement": False,
        "delete_allowed": False,
        "platform_publish_allowed": False,
        "external_action_allowed": False,
        "human_required": bool(blockers),
        "human_reason": "HIGH_RISK" if blockers else None,
    }

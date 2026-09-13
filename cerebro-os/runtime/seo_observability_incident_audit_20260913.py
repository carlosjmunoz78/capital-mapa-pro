from __future__ import annotations

# Read-only Make evidence captured 2026-09-13.
# No scenario activation, edit or external mutation is authorized by this module.

SCENARIOS = {
    9597710: {
        "status": "active",
        "retained_success_runs": 4,
        "retained_error_runs": 0,
        "incomplete_executions": 0,
        "connection_statuses": ("ok", "ok"),
        "explicit_error_handler_or_alert_path_observed": False,
    },
    9550706: {
        "status": "active",
        "retained_success_runs": 1,
        "retained_error_runs": 0,
        "incomplete_executions": 0,
        "connection_statuses": ("ok",),
        "explicit_error_handler_or_alert_path_observed": False,
    },
}


def assess() -> dict:
    retained_success = sum(row["retained_success_runs"] for row in SCENARIOS.values())
    retained_errors = sum(row["retained_error_runs"] for row in SCENARIOS.values())
    all_connections_ok = all(all(s == "ok" for s in row["connection_statuses"]) for row in SCENARIOS.values())
    incident_path = all(row["explicit_error_handler_or_alert_path_observed"] for row in SCENARIOS.values())
    return {
        "scenario_count": len(SCENARIOS),
        "retained_success_runs": retained_success,
        "retained_error_runs": retained_errors,
        "incomplete_executions": sum(row["incomplete_executions"] for row in SCENARIOS.values()),
        "all_connections_ok": all_connections_ok,
        "retained_health_evidence_green": retained_success == 5 and retained_errors == 0 and all_connections_ok,
        "incident_capture_path_proven": incident_path,
        "scenario_mutation_performed": False,
        "seo_incident_observability_green": incident_path,
        "status": "SEO_RETAINED_HEALTH_GREEN_INCIDENT_CAPTURE_PATH_NOT_PROVEN",
    }

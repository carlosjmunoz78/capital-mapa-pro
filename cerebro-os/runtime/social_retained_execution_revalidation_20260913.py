from __future__ import annotations

# Live Make read-only revalidation on 2026-09-13.
# No scenario was activated or run and no external platform was mutated.

FACEBOOK_BASELINE = {
    "scenario_id": 9527908,
    "status": "inactive",
    "connection_status": "ok",
    "read_only_design": True,
    "retained_execution_count": 2,
}

SCENARIOS = {
    "linkedin": {
        "scenario_id": 9522860,
        "status": "inactive",
        "connection_status": "ok",
        "read_only_design": True,
        "retained_execution_count": 0,
    },
    "youtube": {
        "scenario_id": 9537666,
        "status": "inactive",
        "connection_status": "ok",
        "read_only_design": True,
        "retained_execution_count": 0,
    },
}


def assess() -> dict:
    absent = tuple(name for name, row in SCENARIOS.items() if row["retained_execution_count"] == 0)
    valid_config = tuple(
        name for name, row in SCENARIOS.items()
        if row["connection_status"] == "ok" and row["read_only_design"]
    )
    return {
        "scenario_count": len(SCENARIOS),
        "platforms_with_valid_read_only_configuration": valid_config,
        "platforms_without_retained_execution": absent,
        "facebook_metric_execution_proven": FACEBOOK_BASELINE["retained_execution_count"] > 0,
        "linkedin_metric_execution_proven": SCENARIOS["linkedin"]["retained_execution_count"] > 0,
        "youtube_metric_execution_proven": SCENARIOS["youtube"]["retained_execution_count"] > 0,
        "explicit_external_absence_proven": absent == ("linkedin", "youtube"),
        "absence_explained_by_current_inactive_state": all(SCENARIOS[name]["status"] == "inactive" for name in absent),
        "scenario_activation_performed": False,
        "scenario_run_performed": False,
        "external_mutation_performed": False,
        "social_observability_green": False,
        "status": "LINKEDIN_YOUTUBE_CONFIGURATION_VALID_RETAINED_EXECUTION_ABSENT_FACEBOOK_BASELINE_PRESENT",
    }

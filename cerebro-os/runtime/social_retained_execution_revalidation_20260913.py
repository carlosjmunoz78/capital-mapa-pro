from __future__ import annotations

# Live Make read-only revalidation on 2026-09-13.
# No scenario was activated or run and no external platform was mutated.

SCENARIOS = {
    "linkedin": {"scenario_id": 9522860, "retained_execution_count": 0},
    "youtube": {"scenario_id": 9537666, "retained_execution_count": 0},
}


def assess() -> dict:
    absent = tuple(name for name, row in SCENARIOS.items() if row["retained_execution_count"] == 0)
    return {
        "scenario_count": len(SCENARIOS),
        "platforms_without_retained_execution": absent,
        "linkedin_metric_execution_proven": SCENARIOS["linkedin"]["retained_execution_count"] > 0,
        "youtube_metric_execution_proven": SCENARIOS["youtube"]["retained_execution_count"] > 0,
        "explicit_external_absence_proven": absent == ("linkedin", "youtube"),
        "scenario_activation_performed": False,
        "scenario_run_performed": False,
        "external_mutation_performed": False,
        "social_observability_green": False,
        "status": "LINKEDIN_YOUTUBE_RETAINED_EXECUTION_ABSENCE_REVALIDATED",
    }

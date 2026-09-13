from __future__ import annotations

# Live read-only evidence revalidated from Make folder 520866 on 2026-09-13.
# This file records what was observed; it does not activate scenarios or mutate external systems.

FACEBOOK_METRICS_SCENARIO = {
    "scenario_id": 9527908,
    "name": "FENIX · HEALTH · Facebook Pages · Métricas base · V1",
    "status": "inactive",
    "mode": "READ_ONLY",
    "incomplete_executions": 0,
    "retained_runs": (
        {
            "execution_id": "58377db399ae49a4b0d8bc8b40d86e02",
            "started_at": "2026-08-18T15:45:12.128Z",
            "status": "success",
            "operations": 3,
            "credits": 3,
            "data_transfer": 604,
        },
        {
            "execution_id": "696bf528a87c437abdd06bff6a64d05a",
            "started_at": "2026-08-18T15:00:17.505Z",
            "status": "success",
            "operations": 3,
            "credits": 3,
            "data_transfer": 604,
        },
    ),
}

OTHER_SOCIAL_HEALTH = {
    "linkedin": {"scenario_id": 9522860, "status": "inactive", "retained_run_count": 0},
    "youtube": {"scenario_id": 9537666, "status": "inactive", "retained_run_count": 0},
}


def assess_social_live_metrics() -> dict:
    runs = FACEBOOK_METRICS_SCENARIO["retained_runs"]
    facebook_live_metrics_proven = bool(runs) and all(run["status"] == "success" for run in runs)
    total_operations = sum(run["operations"] for run in runs)
    total_credits = sum(run["credits"] for run in runs)
    total_transfer = sum(run["data_transfer"] for run in runs)
    cross_network_complete = all(row["retained_run_count"] > 0 for row in OTHER_SOCIAL_HEALTH.values())
    return {
        "facebook_live_metrics_proven": facebook_live_metrics_proven,
        "facebook_successful_runs": len(runs),
        "facebook_operations_observed": total_operations,
        "facebook_credits_observed": total_credits,
        "facebook_data_transfer_observed": total_transfer,
        "linkedin_live_metrics_proven": OTHER_SOCIAL_HEALTH["linkedin"]["retained_run_count"] > 0,
        "youtube_live_metrics_proven": OTHER_SOCIAL_HEALTH["youtube"]["retained_run_count"] > 0,
        "cross_network_metrics_complete": cross_network_complete,
        "social_metrics_green": facebook_live_metrics_proven and cross_network_complete,
        "scenario_activation_performed": False,
        "external_mutation_performed": False,
        "monthly_cost_eur": None,
        "cost_measured_green": False,
        "prod_candidate_allowed": False,
        "status": "FACEBOOK_LIVE_METRICS_PROVEN_SOCIAL_COVERAGE_PARTIAL" if facebook_live_metrics_proven else "SOCIAL_LIVE_METRICS_PENDING",
    }

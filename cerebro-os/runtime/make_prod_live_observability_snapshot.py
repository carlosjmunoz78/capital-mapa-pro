from __future__ import annotations

SNAPSHOT = {
    "captured_at": "2026-09-13",
    "team_id": 1927480,
    "prod_folder_id": 520863,
    "active_scenarios": {
        9597710: {
            "name": "FÉNIX · PROD · SEO · GSC 30d → Inventario Notion · V2",
            "credits_total_snapshot": 506,
            "data_transfer_total_snapshot": 2802729,
            "successful_runs": (
                {"started_at": "2026-09-09T11:37:00.032Z", "operations": 147, "credits": 147, "data_transfer": 736938},
                {"started_at": "2026-09-02T11:37:01.708Z", "operations": 150, "credits": 150, "data_transfer": 764413},
                {"started_at": "2026-08-26T11:36:58.541Z", "operations": 117, "credits": 117, "data_transfer": 711693},
                {"started_at": "2026-08-19T11:37:02.646Z", "operations": 92, "credits": 92, "data_transfer": 589685},
            ),
        },
        9550706: {
            "name": "FÉNIX · PROD · SEO · Search Console · Vigilancia semanal · V1",
            "credits_total_snapshot": 1,
            "data_transfer_total_snapshot": 162307,
            "successful_runs": (
                {"started_at": "2026-09-07T07:33:32.652Z", "operations": 1, "credits": 1, "data_transfer": 162307},
            ),
        },
    },
}


def assess_make_prod_observability() -> dict:
    runs = [run for scenario in SNAPSHOT["active_scenarios"].values() for run in scenario["successful_runs"]]
    return {
        "active_scenario_count": len(SNAPSHOT["active_scenarios"]),
        "successful_run_count": len(runs),
        "operations_observed": sum(run["operations"] for run in runs),
        "credits_observed": sum(run["credits"] for run in runs),
        "data_transfer_observed": sum(run["data_transfer"] for run in runs),
        "live_execution_evidence_green": bool(runs),
        "monthly_invoice_cost_measured": False,
        "prod_candidate_allowed": False,
        "status": "LIVE_EXECUTION_EVIDENCE_GREEN_MONTHLY_COST_PENDING",
    }

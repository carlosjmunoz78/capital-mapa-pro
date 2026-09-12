from __future__ import annotations

PROJECT_ID = "cluhljgonannaafpmblx"

PROD_TABLE_EVIDENCE = {
    "activity_log": {"estimated_rows": 24, "evidence_kind": "LOGS"},
    "daily_report_snapshots": {"estimated_rows": 2, "evidence_kind": "METRICS_REPORTING"},
    "document_intelligence_runs": {"estimated_rows": 66, "evidence_kind": "ENGINE_RUNS"},
    "lead_events": {"estimated_rows": 2, "evidence_kind": "EVENTS"},
    "notification_state": {"estimated_rows": 3, "evidence_kind": "INCIDENT_NOTIFICATION_STATE"},
    "runtime_policies": {"estimated_rows": -1, "evidence_kind": "POLICY_TABLE_PRESENT"},
}


def assess_prod_observability() -> dict:
    present = tuple(sorted(PROD_TABLE_EVIDENCE))
    has_logs = "activity_log" in PROD_TABLE_EVIDENCE
    has_metrics = "daily_report_snapshots" in PROD_TABLE_EVIDENCE
    has_engine_runs = "document_intelligence_runs" in PROD_TABLE_EVIDENCE
    has_incident_state = "notification_state" in PROD_TABLE_EVIDENCE
    return {
        "project_id": PROJECT_ID,
        "read_only_live_verified": True,
        "tables_present": present,
        "logs_evidence_present": has_logs,
        "metrics_reporting_evidence_present": has_metrics,
        "engine_run_evidence_present": has_engine_runs,
        "incident_state_evidence_present": has_incident_state,
        "monthly_cost_eur": None,
        "cost_measured_green": False,
        "per_engine_coverage_proven": False,
        "observability_green": False,
        "prod_candidate_allowed": False,
        "prod_mutation_performed": False,
        "status": "LIVE_OBSERVABILITY_PARTIAL_COST_AND_PER_ENGINE_COVERAGE_PENDING",
    }

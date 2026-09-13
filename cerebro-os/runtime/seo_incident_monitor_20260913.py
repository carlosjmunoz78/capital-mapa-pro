from __future__ import annotations

# Zero-cost, non-mutating incident classification for existing SEO scenario runs.
# It does not edit, activate or execute Make scenarios. It only classifies evidence
# supplied by the existing run-history adapter and returns a scoped incident envelope.

SEO_SCENARIOS = {9597710, 9550706}


def classify_run(*, scenario_id: int, status: str, company_id: str, engine_id: str, environment: str, version: str, execution_id: str) -> dict:
    if scenario_id not in SEO_SCENARIOS:
        raise ValueError("unknown_seo_scenario")
    if not all((company_id, engine_id, environment, version, execution_id)):
        raise ValueError("missing_scope_or_execution")
    normalized = status.lower().strip()
    if normalized not in {"success", "warning", "error", "pending"}:
        raise ValueError("unsupported_status")
    incident = normalized in {"warning", "error"}
    return {
        "company_id": company_id,
        "engine_id": engine_id,
        "environment": environment,
        "version": version,
        "scenario_id": scenario_id,
        "execution_id": execution_id,
        "status": normalized,
        "incident": incident,
        "severity": "HIGH" if normalized == "error" else ("MEDIUM" if normalized == "warning" else None),
        "external_mutation_performed": False,
        "make_scenario_mutation_allowed": False,
    }


def assess_current_retained_evidence() -> dict:
    # Current read-only snapshot: 5 retained runs across the two active SEO scenarios,
    # all successful, zero errors and zero incomplete executions.
    return {
        "retained_run_count": 5,
        "retained_success_count": 5,
        "retained_incident_count": 0,
        "incident_classifier_ready": True,
        "make_native_error_handler_present": False,
        "parallel_zero_cost_incident_path_ready_in_code": True,
        "prod_wiring_enabled": False,
        "seo_incident_observability_green": False,
        "next_gate": "WIRE_READ_ONLY_RUN_EVIDENCE_TO_PARALLEL_MONITOR_AND_PROVE_INCIDENT_CAPTURE_WITH_NON_PROD_FIXTURE",
    }

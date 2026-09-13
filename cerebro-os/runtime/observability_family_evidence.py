from __future__ import annotations

COMPANY_ID = "fenix_capital"
ENVIRONMENT = "PROD"

# Evidence is intentionally conservative: table presence and aggregate rows prove
# that a surface emits operational evidence, but not that every engine in the family
# has complete logs/metrics/incidents/cost coverage.
FAMILY_EVIDENCE = {
    "app_crm": {
        "logs_ref": "fenix_prod.activity_log",
        "metrics_ref": "fenix_prod.daily_report_snapshots",
        "incident_ref": "fenix_prod.notification_state",
        "cost_ref": "",
        "live_examples": ("clientes", "tareas", "expediente_stage"),
    },
    "document_intelligence": {
        "logs_ref": "fenix_prod.document_intelligence_runs",
        "metrics_ref": "fenix_prod.document_intelligence_runs:status_aggregate",
        "incident_ref": "fenix_prod.notification_state",
        "cost_ref": "",
        "live_examples": ("applied=65", "needs_review=1"),
    },
    "lead_ingest": {
        "logs_ref": "fenix_prod.lead_events",
        "metrics_ref": "fenix_prod.lead_events:status_aggregate",
        "incident_ref": "fenix_prod.notification_state",
        "cost_ref": "",
        "live_examples": ("accepted=3",),
    },
    "daily_reporting": {
        "logs_ref": "fenix_prod.activity_log",
        "metrics_ref": "fenix_prod.daily_report_snapshots",
        "incident_ref": "fenix_prod.notification_state",
        "cost_ref": "",
        "live_examples": ("company_completed=2", "actor_completed=1"),
    },
    "seo": {
        "logs_ref": "MAKE_PROD_GSC_SCENARIOS_AUDITED",
        "metrics_ref": "MAKE_PROD_GSC_READ_ONLY_EDGES",
        "incident_ref": "",
        "cost_ref": "",
        "live_examples": (),
    },
    "social": {
        "logs_ref": "MAKE_CORE_AND_PROD_INVENTORY_AUDITED",
        "metrics_ref": "",
        "incident_ref": "MAKE_ALERT_HEALTH_FOLDER_AUDITED",
        "cost_ref": "",
        "live_examples": (),
    },
    "engine_factory": {
        "logs_ref": "GITHUB_ACTIONS_ENGINE_FACTORY_V0",
        "metrics_ref": "GITHUB_ACTIONS_TEST_RESULTS",
        "incident_ref": "",
        "cost_ref": "",
        "live_examples": (),
    },
}

CHECK_FIELDS = {
    "logs": "logs_ref",
    "metrics": "metrics_ref",
    "incidents": "incident_ref",
    "cost_measured": "cost_ref",
}


def assess_family(name: str) -> dict:
    if name not in FAMILY_EVIDENCE:
        raise KeyError(name)
    row = FAMILY_EVIDENCE[name]
    checks = {check: bool(str(row[field]).strip()) for check, field in CHECK_FIELDS.items()}
    missing = tuple(k for k, ok in checks.items() if not ok)
    return {
        "company_id": COMPANY_ID,
        "family": name,
        "environment": ENVIRONMENT,
        "checks": checks,
        "missing": missing,
        "green": not missing,
        "prod_candidate_allowed": False,
        "monthly_cost_eur": None,
        "money_limit_triggered": False,
        "human_reason": None,
        "additional_paid_ai_required": False,
    }


def assess_all_families() -> dict:
    assessed = {name: assess_family(name) for name in FAMILY_EVIDENCE}
    green = tuple(name for name, row in assessed.items() if row["green"])
    pending = tuple(name for name, row in assessed.items() if not row["green"])
    return {
        "families": assessed,
        "green_families": green,
        "pending_families": pending,
        "all_green": not pending,
        "prod_candidate_allowed": False,
        "cost_measurement_pending": True,
        "status": "OBSERVABILITY_FAMILY_EVIDENCE_PARTIAL",
    }

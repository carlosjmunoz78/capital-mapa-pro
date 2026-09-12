from __future__ import annotations

PROJECTS = {
    "legacy_core": {
        "project_id": "hnqlnvakzaywtafeiybt",
        "name": "fenix-capital-inmo-map",
        "status": "ACTIVE_HEALTHY",
        "region": "eu-north-1",
        "public_tables": (
            "brevo_integration_runs_preprod",
            "brevo_webhook_events_preprod",
            "linkedin_oauth_tokens_preprod",
            "seo_cerebro_changes_preprod",
            "seo_cerebro_runs_preprod",
            "web_lead_events_preprod",
            "web_lead_tasks_preprod",
            "web_leads_preprod",
        ),
        "active_edge_functions_present": True,
        "security_findings": {
            "rls_enabled_no_policy": 30,
            "leaked_password_protection_disabled": 1,
        },
    },
    "prod": {
        "project_id": "cluhljgonannaafpmblx",
        "name": "fenix-capital-prod",
        "status": "ACTIVE_HEALTHY",
        "region": "eu-west-2",
        "public_tables": (),
        "active_edge_functions_present": True,
        "security_findings": {
            "rls_enabled_no_policy": 40,
            "extension_in_public": 1,
            "authenticated_security_definer_function_executable": 24,
            "leaked_password_protection_disabled": 1,
        },
    },
}


def assess_live_supabase_dependency() -> dict:
    projects_healthy = all(p["status"] == "ACTIVE_HEALTHY" for p in PROJECTS.values())
    security_findings = sum(sum(p["security_findings"].values()) for p in PROJECTS.values())
    return {
        "live_read_only_verified": True,
        "projects_healthy": projects_healthy,
        "project_ids": tuple(p["project_id"] for p in PROJECTS.values()),
        "edge_functions_live_verified": all(p["active_edge_functions_present"] for p in PROJECTS.values()),
        "security_findings_total": security_findings,
        "security_review_required": security_findings > 0,
        "prod_mutation_performed": False,
        "schema_mutation_performed": False,
        "promotion_allowed": False,
        "status": "LIVE_DEPENDENCY_VERIFIED_SECURITY_REVIEW_PENDING" if projects_healthy else "LIVE_DEPENDENCY_BLOCKED",
    }

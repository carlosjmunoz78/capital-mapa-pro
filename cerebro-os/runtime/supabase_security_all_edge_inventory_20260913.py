from __future__ import annotations

# Read-only snapshot of every current Edge Function listed in PROD on 2026-09-13.
# Evidence-only: no function was deployed, invoked, disabled, deleted, or modified.

TOTAL_PROD_PROJECT_EDGE_SURFACES = 38
PREVIOUSLY_INSPECTED_SECURITY_EDGE_SURFACES = 33
NEWLY_INSPECTED_SURFACES = {
    "fenix-directory-sync-trigger-once": "HTTP_410_RETIRED",
    "fenix-crm-sync-once": "HTTP_410_RETIRED",
    "fenix-crm-sync-trigger-once": "HTTP_410_RETIRED",
    "fenix-prod-data-sync-once": "HTTP_410_RETIRED",
    "fenix-document-intelligence-test": "AUTHENTICATED_TEST_ROUTE_FAILS_CLOSED_TO_TEST_RESPONSE",
}


def assess() -> dict:
    retired_count = sum(1 for value in NEWLY_INSPECTED_SURFACES.values() if value == "HTTP_410_RETIRED")
    return {
        "total_prod_project_edge_surfaces": TOTAL_PROD_PROJECT_EDGE_SURFACES,
        "previously_inspected_security_edge_surfaces": PREVIOUSLY_INSPECTED_SECURITY_EDGE_SURFACES,
        "newly_inspected_surface_count": len(NEWLY_INSPECTED_SURFACES),
        "newly_inspected_retired_410_count": retired_count,
        "all_current_edge_surfaces_now_accounted_for": PREVIOUSLY_INSPECTED_SECURITY_EDGE_SURFACES + len(NEWLY_INSPECTED_SURFACES) == TOTAL_PROD_PROJECT_EDGE_SURFACES,
        "direct_client_mutator_retirement_authorized": False,
        "global_caller_absence_proven": False,
        "prod_edge_modified": False,
        "prod_privilege_change_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "status": "ALL_CURRENT_PROD_PROJECT_EDGE_SURFACES_ACCOUNTED_FOR_FAIL_CLOSED",
    }

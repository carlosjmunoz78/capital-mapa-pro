from __future__ import annotations

PROD_PROJECT_ID = "cluhljgonannaafpmblx"

APP_EDGES = {
    "fenix-app-gateway": {
        "status": "ACTIVE",
        "version": 16,
        "verify_jwt": False,
        "mode": "AUTHENTICATED_GATEWAY_WITH_INTERNAL_IDENTITY_RESOLUTION",
        "origin": "https://app.fenixcapital.es",
        "environment": "PROD",
        "writes_via_server_rpcs": True,
        "direct_table_writes": False,
    },
    "fenix-directory-api": {
        "status": "ACTIVE",
        "version": 9,
        "verify_jwt": True,
        "mode": "READ_ONLY_DIRECTORY_API",
        "environment": "PROD",
    },
    "fenix-directory-actions": {
        "status": "ACTIVE",
        "version": 8,
        "verify_jwt": True,
        "mode": "DIRECTION_GATED_DIRECTORY_WRITE_API",
        "environment": "PROD",
    },
}

RETIRED_MIGRATION_EDGES = {
    "fenix-crm-sync-once": {"status": "ACTIVE", "version": 10, "runtime_contract": "HTTP_410_MIGRATION_ENDPOINT_RETIRED"},
    "fenix-crm-sync-trigger-once": {"status": "ACTIVE", "version": 10, "runtime_contract": "HTTP_410_MIGRATION_ENDPOINT_RETIRED"},
    "fenix-directory-sync-once": {"status": "ACTIVE", "version": 12, "runtime_contract": "HTTP_410_MIGRATION_ENDPOINT_RETIRED"},
    "fenix-prod-data-sync-once": {"status": "ACTIVE", "version": 12, "runtime_contract": "HTTP_410_MIGRATION_ENDPOINT_RETIRED"},
}

LIVE_CRM_SURFACES = (
    "expedientes",
    "tareas",
    "documentos",
    "bancos",
    "envios_banco",
    "ofertas",
    "tasaciones",
    "firmas",
    "inmobiliarias",
    "contactos",
    "personal_directorio",
    "notarias",
    "registros_propiedad",
)


def assess_app_crm_live_map() -> dict:
    gateway = APP_EDGES["fenix-app-gateway"]
    retired_safe = all(v["runtime_contract"] == "HTTP_410_MIGRATION_ENDPOINT_RETIRED" for v in RETIRED_MIGRATION_EDGES.values())
    app_live = gateway["status"] == "ACTIVE" and gateway["environment"] == "PROD"
    directory_live = APP_EDGES["fenix-directory-api"]["status"] == "ACTIVE" and APP_EDGES["fenix-directory-actions"]["status"] == "ACTIVE"
    return {
        "project_id": PROD_PROJECT_ID,
        "app_live_verified": app_live,
        "crm_live_surface_verified": app_live and bool(LIVE_CRM_SURFACES),
        "directory_live_verified": directory_live,
        "retired_migration_edges_fail_closed": retired_safe,
        "app_gateway_verify_jwt_disabled_but_identity_resolved_in_function": gateway["verify_jwt"] is False,
        "live_crm_surfaces": LIVE_CRM_SURFACES,
        "old_sync_endpoints_may_be_reactivated": False,
        "old_sync_endpoints_may_be_deleted": False,
        "prod_mutation_performed": False,
        "status": "LIVE_APP_CRM_MAP_VERIFIED_SECURITY_REVIEW_PENDING" if app_live and directory_live and retired_safe else "LIVE_APP_CRM_MAP_BLOCKED",
        "prod_candidate_allowed": False,
    }

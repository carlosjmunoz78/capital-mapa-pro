from __future__ import annotations

REQUIRED_SYSTEMS = ("app", "crm", "supabase", "notion", "wordpress", "seo")

# Canonical historical sources. These are evidence references, not proof that current live state is unchanged.
HISTORICAL_EVIDENCE = {
    "repo_inventory": "REPO_INVENTORY_CEREBRO_2026-09-05.md",
    "app_contract": "APP_CONTRACT_MATRIX_CEREBRO_2026-09-05.md",
    "supabase_contract": "SUPABASE_SYSTEM_CONTRACT_MAP_2026-09-05.md",
    "bootstrap": "CEREBRO_PROJECT_BOOTSTRAP_MANIFEST_V1.1_2026-09-07.md",
}

SYSTEM_STATUS = {
    "app": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": True,
        "verification_scope": "PROD_EDGE_FUNCTION_CONTRACT",
        "promotion_blockers": ("SUPABASE_SECURITY_REVIEW",),
        "notes": "PROD fenix-app-gateway and directory edges were read-only audited; no production mutation was executed.",
    },
    "crm": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": True,
        "verification_scope": "PROD_RPC_AND_EDGE_SURFACE",
        "promotion_blockers": ("SUPABASE_SECURITY_REVIEW",),
        "notes": "Live CRM surface was mapped through App Gateway/server RPCs; retired migration sync endpoints return HTTP 410 and remain preserved.",
    },
    "supabase": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": True,
        "verification_scope": "PROJECTS_EDGE_FUNCTIONS_TABLES_ADVISORS_READ_ONLY",
        "promotion_blockers": ("SUPABASE_SECURITY_REVIEW",),
        "notes": "Both Supabase projects are ACTIVE_HEALTHY and live state was read-only verified; security advisor findings remain unresolved.",
    },
    "notion": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": True,
        "verification_scope": "PREPROD_TEST_CANONICAL_RUNTIME",
        "promotion_blockers": (),
        "notes": "Canonical Notion PREPROD_TEST reader is live and role-scoped; deprecated bridge returns HTTP 410 and remains preserved.",
    },
    "wordpress": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": True,
        "verification_scope": "PREPROD_DRAFT_ONLY_RUNTIME",
        "promotion_blockers": ("PROD_WRITE_NOT_EXERCISED",),
        "notes": "WordPress PREPROD adapter is live, draft-only and rollback-capable. No production publish was executed or inferred.",
    },
    "seo": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": True,
        "verification_scope": "PREPROD_EXECUTOR_PLUS_PROD_READ_ONLY_GSC",
        "promotion_blockers": (),
        "notes": "SEO PREPROD executor is allowlisted/draft-only with verification+rollback; two active GSC PROD edges remain read-only and preserved.",
    },
}


def assess_dependency_snapshot() -> dict:
    missing_systems = tuple(system for system in REQUIRED_SYSTEMS if system not in SYSTEM_STATUS)
    inventory_complete = not missing_systems and all(SYSTEM_STATUS[s]["inventory"] for s in REQUIRED_SYSTEMS)
    historical_contracts_complete = all(SYSTEM_STATUS[s]["historical_contract"] for s in REQUIRED_SYSTEMS)
    live_unverified = tuple(s for s in REQUIRED_SYSTEMS if not SYSTEM_STATUS[s]["live_verified_current"])
    promotion_blockers = tuple(
        f"{system}:{blocker}"
        for system in REQUIRED_SYSTEMS
        for blocker in SYSTEM_STATUS[system].get("promotion_blockers", ())
    )
    live_dependency_verified = inventory_complete and historical_contracts_complete and not live_unverified
    promotion_ready = live_dependency_verified and not promotion_blockers
    return {
        "required_systems": REQUIRED_SYSTEMS,
        "missing_systems": missing_systems,
        "inventory_complete": inventory_complete,
        "historical_contracts_complete": historical_contracts_complete,
        "live_unverified": live_unverified,
        "live_dependency_verified": live_dependency_verified,
        "promotion_blockers": promotion_blockers,
        "dependency_green": live_dependency_verified,
        "promotion_ready": promotion_ready,
        "prod_candidate_allowed": False,
        "old_systems_may_be_deleted": False,
        "parallel_migration_required": True,
        "migration_rule": "CONSERVAR_ENTENDER_ENVOLVER_PROBAR_MEJORAR_MIGRAR",
        "historical_evidence": dict(HISTORICAL_EVIDENCE),
    }

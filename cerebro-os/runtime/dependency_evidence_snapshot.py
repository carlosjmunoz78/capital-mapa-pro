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
        "live_verified_current": False,
        "notes": "App implementation historically inventoried; current HEAD/deployment must be reverified before promotion.",
    },
    "crm": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": False,
        "notes": "CRM spans Supabase, App and transitional Notion; source-of-truth and writers/readers remain live-verification items.",
    },
    "supabase": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": False,
        "notes": "Historical map records tables/functions and overlaps; current callers/RPC/Edge state must be reverified.",
    },
    "notion": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": False,
        "notes": "Existing Make/Notion edges are preserved; full current writer/reader map is not yet proven here.",
    },
    "wordpress": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": False,
        "notes": "Core Guard repository was historically blocked pending canonical branch/promotion verification.",
    },
    "seo": {
        "inventory": True,
        "historical_contract": True,
        "live_verified_current": True,
        "notes": "Two active GSC PROD read-only edges were re-audited and are preserve-active-edge contracts.",
    },
}


def assess_dependency_snapshot() -> dict:
    missing_systems = tuple(system for system in REQUIRED_SYSTEMS if system not in SYSTEM_STATUS)
    inventory_complete = not missing_systems and all(SYSTEM_STATUS[s]["inventory"] for s in REQUIRED_SYSTEMS)
    historical_contracts_complete = all(SYSTEM_STATUS[s]["historical_contract"] for s in REQUIRED_SYSTEMS)
    live_unverified = tuple(s for s in REQUIRED_SYSTEMS if not SYSTEM_STATUS[s]["live_verified_current"])
    current_live_green = inventory_complete and historical_contracts_complete and not live_unverified
    return {
        "required_systems": REQUIRED_SYSTEMS,
        "missing_systems": missing_systems,
        "inventory_complete": inventory_complete,
        "historical_contracts_complete": historical_contracts_complete,
        "live_unverified": live_unverified,
        "dependency_green": current_live_green,
        "prod_candidate_allowed": False,
        "old_systems_may_be_deleted": False,
        "parallel_migration_required": True,
        "migration_rule": "CONSERVAR_ENTENDER_ENVOLVER_PROBAR_MEJORAR_MIGRAR",
        "historical_evidence": dict(HISTORICAL_EVIDENCE),
    }

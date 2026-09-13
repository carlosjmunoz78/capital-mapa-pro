from __future__ import annotations

PROJECTS = {
    "hnqlnvakzaywtafeiybt": {
        "name": "fenix-capital-inmo-map",
        "status": "ACTIVE_HEALTHY",
        "role": "EXISTING_NON_PROD_WITH_LEGACY_CORE_DEPENDENCY",
        "safe_for_destructive_restore": False,
    },
    "cluhljgonannaafpmblx": {
        "name": "fenix-capital-prod",
        "status": "ACTIVE_HEALTHY",
        "role": "PROD",
        "safe_for_destructive_restore": False,
    },
}

PROD_BRANCHES = {
    "dcfba80a-79bc-4164-8524-447fa6d10893": {
        "name": "main",
        "project_ref": "cluhljgonannaafpmblx",
        "is_default": True,
        "persistent": False,
        "status": "FUNCTIONS_DEPLOYED",
        "with_data": False,
    }
}


def assess() -> dict:
    safe_projects = tuple(k for k, v in PROJECTS.items() if v["safe_for_destructive_restore"])
    non_default_branches = tuple(k for k, v in PROD_BRANCHES.items() if not v["is_default"])
    return {
        "project_count": len(PROJECTS),
        "safe_existing_restore_target_count": len(safe_projects),
        "non_default_branch_count": len(non_default_branches),
        "isolated_restore_target_available_now": bool(safe_projects or non_default_branches),
        "new_paid_resource_created": False,
        "automatic_prod_restore_allowed": False,
        "provider_restore_green": False,
        "status": "NO_EXISTING_SAFE_ISOLATED_RESTORE_TARGET_ZERO_COST_INVENTORY_COMPLETE",
    }

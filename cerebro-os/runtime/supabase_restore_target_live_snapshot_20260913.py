from __future__ import annotations

SNAPSHOT = {
    "fenix_capital_prod": {
        "project_ref": "cluhljgonannaafpmblx",
        "branch_count": 1,
        "default_branch_only": True,
        "isolated_restore_target_present": False,
    },
    "fenix_capital_inmo_map": {
        "project_ref": "hnqlnvakzaywtafeiybt",
        "branch_count": 0,
        "isolated_restore_target_present": False,
    },
}


def assess() -> dict:
    isolated = any(v["isolated_restore_target_present"] for v in SNAPSHOT.values())
    return {
        "projects_observed": len(SNAPSHOT),
        "isolated_restore_target_present": isolated,
        "paid_branch_created": False,
        "provider_restore_green": False,
        "status": "NO_ISOLATED_RESTORE_TARGET_PRESENT_COST_CONFIRMATION_REQUIRED_BEFORE_BRANCH_CREATION",
    }

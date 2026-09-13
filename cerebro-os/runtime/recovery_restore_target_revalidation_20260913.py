from __future__ import annotations

# Read-only provider inventory revalidation captured 2026-09-13.
# No project pause, restore, branch creation, destructive reset, merge, or PROD mutation is authorized.

PROD_PROJECT = {
    "project_id": "cluhljgonannaafpmblx",
    "status": "ACTIVE_HEALTHY",
    "default_branch_count": 1,
    "isolated_nondefault_branch_count": 0,
}

LEGACY_PROJECT = {
    "project_id": "hnqlnvakzaywtafeiybt",
    "status": "ACTIVE_HEALTHY",
    "branch_count": 0,
    "safe_destructive_restore_target": False,
}


def assess() -> dict:
    isolated_target = PROD_PROJECT["isolated_nondefault_branch_count"] > 0
    provider_restore_safe_now = isolated_target and LEGACY_PROJECT["safe_destructive_restore_target"] is False
    return {
        "prod_active_healthy": PROD_PROJECT["status"] == "ACTIVE_HEALTHY",
        "legacy_active_healthy": LEGACY_PROJECT["status"] == "ACTIVE_HEALTHY",
        "prod_default_branch_count": PROD_PROJECT["default_branch_count"],
        "prod_isolated_nondefault_branch_count": PROD_PROJECT["isolated_nondefault_branch_count"],
        "legacy_branch_count": LEGACY_PROJECT["branch_count"],
        "isolated_restore_target_available": isolated_target,
        "legacy_destructive_restore_allowed": False,
        "prod_destructive_restore_allowed": False,
        "provider_restore_safe_now": provider_restore_safe_now,
        "restore_project_tool_may_be_invoked_now": False,
        "recovery_green": False,
        "status": "NO_ISOLATED_RESTORE_TARGET_RESTORE_TOOL_FAIL_CLOSED",
    }

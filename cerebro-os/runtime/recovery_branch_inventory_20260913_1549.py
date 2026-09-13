SNAPSHOT = {
    "captured_at": "2026-09-13",
    "prod_project": "cluhljgonannaafpmblx",
    "prod_branches": ("main",),
    "legacy_project": "hnqlnvakzaywtafeiybt",
    "legacy_branches": (),
    "isolated_restore_target_available": False,
    "restore_attempted": False,
    "existing_projects_modified": False,
}


def assess_recovery_branch_inventory() -> dict:
    return {
        **SNAPSHOT,
        "recovery_restore_green": False,
        "status": "NO_ISOLATED_RESTORE_TARGET",
    }

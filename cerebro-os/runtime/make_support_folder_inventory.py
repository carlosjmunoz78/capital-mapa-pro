from __future__ import annotations

FOLDERS = {
    520861: {
        "name": "AUDIT_LEGACY",
        "expected_ids": {
            9527814, 5565247, 5566037, 9531064, 9528012, 9538815, 9522933, 9522994, 9522583
        },
        "auto_activate_allowed": False,
        "delete_allowed": False,
    },
    520865: {
        "name": "PREVENTIVE_RECOVERY",
        "expected_ids": {9527263, 9524813},
        "auto_activate_allowed": False,
        "delete_allowed": False,
    },
    520866: {
        "name": "ALERTS_HEALTH",
        "expected_ids": {9527636, 9527843, 9527663, 9527908, 9522860, 9527602, 9527718, 9537666},
        "auto_activate_allowed": False,
        "delete_allowed": False,
    },
}


def validate_folder(folder_id: int, live_ids: set[int]) -> dict:
    if folder_id not in FOLDERS:
        raise ValueError("unknown support folder")
    cfg = FOLDERS[folder_id]
    expected = cfg["expected_ids"]
    missing = tuple(sorted(expected - live_ids))
    unexpected = tuple(sorted(live_ids - expected))
    return {
        "folder_id": folder_id,
        "name": cfg["name"],
        "expected_count": len(expected),
        "live_count": len(live_ids),
        "missing": missing,
        "unexpected": unexpected,
        "inventory_green": not missing and not unexpected,
        "auto_activate_allowed": cfg["auto_activate_allowed"],
        "delete_allowed": cfg["delete_allowed"],
    }


def total_expected() -> int:
    return sum(len(v["expected_ids"]) for v in FOLDERS.values())

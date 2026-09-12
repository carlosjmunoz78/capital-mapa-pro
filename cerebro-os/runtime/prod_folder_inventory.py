from __future__ import annotations

PROD_FOLDER_EXPECTED = {
    9721473: ("ONE_SHOT", "FACEBOOK", "PRESERVE_INACTIVE"),
    9721479: ("ONE_SHOT", "INSTAGRAM", "PRESERVE_INACTIVE"),
    9533967: ("SOCIAL_PROD", "FACEBOOK", "RUNTIME_PARITY"),
    9533584: ("SOCIAL_PROD", "FACEBOOK", "PRESERVE_COMPONENT"),
    9533974: ("SOCIAL_PROD", "FACEBOOK", "RUNTIME_PARITY"),
    9522713: ("SOCIAL_LEGACY", "FACEBOOK", "PRESERVE_INACTIVE"),
    9533532: ("SOCIAL_PROD", "FACEBOOK", "RUNTIME_PARITY"),
    9533724: ("SOCIAL_PROD", "FACEBOOK", "RUNTIME_PARITY"),
    9533715: ("SOCIAL_PROD", "FACEBOOK", "RUNTIME_PARITY"),
    9533564: ("SOCIAL_PROD", "FACEBOOK", "RUNTIME_PARITY"),
    9533972: ("SOCIAL_PROD", "FACEBOOK", "RUNTIME_PARITY"),
    9534084: ("SOCIAL_PROD", "INSTAGRAM", "RUNTIME_PARITY"),
    9534139: ("SOCIAL_PROD", "INSTAGRAM", "RUNTIME_PARITY"),
    9534087: ("SOCIAL_PROD", "INSTAGRAM", "RUNTIME_PARITY"),
    9522428: ("SOCIAL_PROD", "LINKEDIN", "RUNTIME_PARITY"),
    9528327: ("SOCIAL_PROD", "LINKEDIN", "RUNTIME_PARITY"),
    5554207: ("SOCIAL_PROD", "LINKEDIN", "RUNTIME_PARITY"),
    9410589: ("SOCIAL_PROD", "LINKEDIN", "RUNTIME_PARITY"),
    9597710: ("SEO_PROD", "GSC_NOTION", "PRESERVE_ACTIVE_EDGE"),
    9550706: ("SEO_PROD", "GSC", "PRESERVE_ACTIVE_EDGE"),
    9537718: ("SOCIAL_PROD", "YOUTUBE_PLAYLIST", "RUNTIME_PARITY"),
    9537710: ("SOCIAL_PROD", "YOUTUBE_THUMBNAIL", "RUNTIME_PARITY"),
    9537699: ("SOCIAL_PROD", "YOUTUBE_SHORT", "RUNTIME_PARITY"),
    9537702: ("SOCIAL_PROD", "YOUTUBE_LONG", "RUNTIME_PARITY"),
    9550846: ("FOLDER_ANOMALY", "WORDPRESS_TEST", "PRESERVE_INACTIVE_RELOCATE_LATER"),
}


def expected_ids() -> set[int]:
    return set(PROD_FOLDER_EXPECTED)


def classify(scenario_id: int) -> dict:
    if scenario_id not in PROD_FOLDER_EXPECTED:
        raise ValueError("unexpected PROD-folder scenario")
    kind, family, target = PROD_FOLDER_EXPECTED[scenario_id]
    return {
        "scenario_id": scenario_id,
        "kind": kind,
        "family": family,
        "target": target,
        "delete_allowed": False,
        "auto_activate_allowed": False,
    }


def validate_inventory(live_ids: set[int]) -> dict:
    expected = expected_ids()
    missing = tuple(sorted(expected - live_ids))
    unexpected = tuple(sorted(live_ids - expected))
    return {
        "expected_count": len(expected),
        "live_count": len(live_ids),
        "missing": missing,
        "unexpected": unexpected,
        "green": not missing and not unexpected and len(live_ids) == 25,
    }

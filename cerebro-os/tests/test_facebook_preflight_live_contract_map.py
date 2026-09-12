import pytest

from runtime.facebook_preflight_live_contract_map import (
    LIVE_PREFLIGHT_MAP,
    all_fail_closed,
    get_live_contract,
)


def test_all_expected_facebook_preflights_are_registered():
    assert set(LIVE_PREFLIGHT_MAP) == {9531078, 9531133, 9533424, 9533987, 9533988, 9533976}


def test_all_contracts_fail_closed_and_preserve_old():
    assert all_fail_closed() is True
    for scenario_id in LIVE_PREFLIGHT_MAP:
        item = get_live_contract(scenario_id)
        assert item["old_preserved"] is True
        assert item["external_action_allowed"] is False
        assert item["autoactivate_old_allowed"] is False
        assert item["delete_old_allowed"] is False
        assert item["prod_cutover_allowed"] is False


def test_link_contract_preserves_direct_read_no_publish_invariant():
    item = get_live_contract(9531078)
    assert item["runtime"] == "facebook_link_preflight.py"
    assert item["invariants"]["platform_state"] == "FACEBOOK_NOT_CALLED"
    assert item["invariants"]["environment"] == "TEST"
    assert "programming" in item["invariants"]["evidence"]


def test_image_contract_requires_asset_and_http_evidence_without_publish():
    item = get_live_contract(9531133)
    assert item["runtime"] == "facebook_image_preflight.py"
    assert item["invariants"]["platform_state"] == "FACEBOOK_NOT_CALLED"
    assert {"asset", "http_head"}.issubset(item["invariants"]["evidence"])


def test_video_short_remains_human_review_evidence_capture():
    item = get_live_contract(9533424)
    assert item["runtime"] == "facebook_video_short_preflight.py"
    assert item["invariants"]["requires_human"] is True
    assert item["invariants"]["platform_state"] == "FACEBOOK_NOT_CALLED"


def test_carousel_exact_live_bounds_are_preserved():
    item = get_live_contract(9533987)
    assert item["runtime"] == "carousel_preflight.py"
    assert item["invariants"]["photo_min"] == 2
    assert item["invariants"]["photo_max"] == 30
    assert item["invariants"]["real_publish_authorized"] is False


def test_long_video_exact_live_bounds_are_preserved():
    item = get_live_contract(9533988)
    assert item["runtime"] == "video_long_preflight.py"
    assert item["invariants"]["http_min"] == 200
    assert item["invariants"]["http_max"] == 399
    assert item["invariants"]["duration_seconds_min_exclusive"] == 90
    assert item["invariants"]["real_publish_authorized"] is False


def test_story_stays_queued_when_provider_is_not_connected():
    item = get_live_contract(9533976)
    assert item["runtime"] == "story_preflight.py"
    assert item["invariants"]["provider_state"] == "NATIVE_CONNECTOR_UNAVAILABLE"
    assert item["invariants"]["queue_status"] == "BLOCKED_PROVIDER_NOT_CONNECTED"
    assert item["invariants"]["requires_human"] is True


def test_unknown_scenario_fails_closed():
    with pytest.raises(ValueError):
        get_live_contract(1)

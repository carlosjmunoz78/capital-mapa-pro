from runtime.social_inactive_router_mapping import MAPPINGS, assess_social_inactive_mapping


def test_expected_inactive_social_scenarios_are_mapped():
    assert {m.scenario_id for m in MAPPINGS} == {9533991, 9534074, 9534077, 9522560, 9537662}


def test_all_mappings_preserve_old_and_forbid_external_action_and_cutover():
    for mapping in MAPPINGS:
        result = assess_social_inactive_mapping(mapping.scenario_id)
        assert result["green"] is True
        assert result["status"] == "MAPPED_RUNTIME_TARGET"
        assert result["old_status"] == "inactive"
        assert result["old_preserved"] is True
        assert result["auto_activate_old"] is False
        assert result["delete_old_allowed"] is False
        assert result["external_action_allowed"] is False
        assert result["prod_cutover_allowed"] is False
        assert result["parity_required"] is True
        assert result["runtime_targets"]


def test_unknown_scenario_fails_closed():
    result = assess_social_inactive_mapping(9999999)
    assert result == {
        "status": "MAPPING_MISSING",
        "green": False,
        "old_preserved": True,
        "external_action_allowed": False,
        "prod_cutover_allowed": False,
    }

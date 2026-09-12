import unittest

from runtime.facebook_preflight_live_contract_map import (
    LIVE_PREFLIGHT_MAP,
    all_fail_closed,
    get_live_contract,
)


class FacebookPreflightLiveContractMapTests(unittest.TestCase):
    def test_all_expected_facebook_preflights_are_registered(self):
        self.assertEqual(set(LIVE_PREFLIGHT_MAP), {9531078, 9531133, 9533424, 9533987, 9533988, 9533976})

    def test_all_contracts_fail_closed_and_preserve_old(self):
        self.assertTrue(all_fail_closed())
        for scenario_id in LIVE_PREFLIGHT_MAP:
            item = get_live_contract(scenario_id)
            self.assertTrue(item["old_preserved"])
            self.assertFalse(item["external_action_allowed"])
            self.assertFalse(item["autoactivate_old_allowed"])
            self.assertFalse(item["delete_old_allowed"])
            self.assertFalse(item["prod_cutover_allowed"])

    def test_link_contract_preserves_direct_read_no_publish_invariant(self):
        item = get_live_contract(9531078)
        self.assertEqual(item["runtime"], "facebook_link_preflight.py")
        self.assertEqual(item["invariants"]["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertEqual(item["invariants"]["environment"], "TEST")
        self.assertIn("programming", item["invariants"]["evidence"])

    def test_image_contract_requires_asset_and_http_evidence_without_publish(self):
        item = get_live_contract(9531133)
        self.assertEqual(item["runtime"], "facebook_image_preflight.py")
        self.assertEqual(item["invariants"]["platform_state"], "FACEBOOK_NOT_CALLED")
        self.assertTrue({"asset", "http_head"}.issubset(item["invariants"]["evidence"]))

    def test_video_short_remains_human_review_evidence_capture(self):
        item = get_live_contract(9533424)
        self.assertEqual(item["runtime"], "facebook_video_short_preflight.py")
        self.assertTrue(item["invariants"]["requires_human"])
        self.assertEqual(item["invariants"]["platform_state"], "FACEBOOK_NOT_CALLED")

    def test_carousel_exact_live_bounds_are_preserved(self):
        item = get_live_contract(9533987)
        self.assertEqual(item["runtime"], "carousel_preflight.py")
        self.assertEqual(item["invariants"]["photo_min"], 2)
        self.assertEqual(item["invariants"]["photo_max"], 30)
        self.assertFalse(item["invariants"]["real_publish_authorized"])

    def test_long_video_exact_live_bounds_are_preserved(self):
        item = get_live_contract(9533988)
        self.assertEqual(item["runtime"], "video_long_preflight.py")
        self.assertEqual(item["invariants"]["http_min"], 200)
        self.assertEqual(item["invariants"]["http_max"], 399)
        self.assertEqual(item["invariants"]["duration_seconds_min_exclusive"], 90)
        self.assertFalse(item["invariants"]["real_publish_authorized"])

    def test_story_stays_queued_when_provider_is_not_connected(self):
        item = get_live_contract(9533976)
        self.assertEqual(item["runtime"], "story_preflight.py")
        self.assertEqual(item["invariants"]["provider_state"], "NATIVE_CONNECTOR_UNAVAILABLE")
        self.assertEqual(item["invariants"]["queue_status"], "BLOCKED_PROVIDER_NOT_CONNECTED")
        self.assertTrue(item["invariants"]["requires_human"])

    def test_unknown_scenario_fails_closed(self):
        with self.assertRaises(ValueError):
            get_live_contract(1)


if __name__ == "__main__":
    unittest.main()

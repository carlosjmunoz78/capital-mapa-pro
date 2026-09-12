import json
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "runtime"))

from replay_parity import ReplayCase, compare_replay


class FacebookLegacyReplayFixtureTests(unittest.TestCase):
    def test_fixture_set_is_green_for_safety_contract(self):
        path = os.path.join(ROOT, "runtime", "fixtures", "facebook_legacy_replay.json")
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        cases = [
            ReplayCase(
                case_id=row["case_id"],
                old_output=row["old_output"],
                new_output=row["new_output"],
                required_equal_fields=tuple(row["required_equal_fields"]),
            )
            for row in payload["cases"]
        ]
        result = compare_replay(cases)
        self.assertTrue(result.green)
        self.assertEqual(3, result.total)
        self.assertEqual(3, result.passed)

    def test_all_legacy_cases_remain_non_mutating(self):
        path = os.path.join(ROOT, "runtime", "fixtures", "facebook_legacy_replay.json")
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for row in payload["cases"]:
            self.assertFalse(row["old_output"]["external_action_allowed"])
            self.assertFalse(row["new_output"]["external_action_allowed"])
            self.assertEqual("FACEBOOK_NOT_CALLED", row["new_output"]["platform_state"])


if __name__ == "__main__":
    unittest.main()

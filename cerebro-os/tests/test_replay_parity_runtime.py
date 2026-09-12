import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from replay_parity import ReplayCase, compare_case, compare_replay


class ReplayParityTests(unittest.TestCase):
    def test_green_when_required_fields_match_and_no_external_action(self):
        case = ReplayCase(
            case_id="fb-link-safe",
            old_output={"platform_state": "FACEBOOK_NOT_CALLED", "status": "DIRECT_CONTRACT_VALIDATED"},
            new_output={"platform_state": "FACEBOOK_NOT_CALLED", "status": "DIRECT_CONTRACT_VALIDATED", "external_action_allowed": False},
            required_equal_fields=("platform_state", "status"),
        )
        self.assertTrue(compare_case(case))
        result = compare_replay([case])
        self.assertTrue(result.green)
        self.assertEqual(1, result.passed)

    def test_mismatch_is_red(self):
        case = ReplayCase(
            case_id="mismatch",
            old_output={"status": "DIRECT_CONTRACT_VALIDATED"},
            new_output={"status": "ROUTED"},
            required_equal_fields=("status",),
        )
        self.assertFalse(compare_case(case))
        self.assertFalse(compare_replay([case]).green)

    def test_external_action_true_is_always_red(self):
        case = ReplayCase(
            case_id="unsafe",
            old_output={"platform_state": "FACEBOOK_NOT_CALLED"},
            new_output={"platform_state": "FACEBOOK_NOT_CALLED", "external_action_allowed": True},
            required_equal_fields=("platform_state",),
        )
        self.assertFalse(compare_case(case))

    def test_empty_replay_is_not_green(self):
        result = compare_replay([])
        self.assertFalse(result.green)
        self.assertEqual(0, result.total)


if __name__ == "__main__":
    unittest.main()

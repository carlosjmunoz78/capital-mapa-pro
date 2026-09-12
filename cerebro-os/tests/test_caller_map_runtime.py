import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from caller_map import CallerEvidence, build_caller_map, can_cut_over_caller


class CallerMapTests(unittest.TestCase):
    def test_complete_map_with_valid_evidence(self):
        result = build_caller_map(
            scenario_id=9530582,
            expected_runtime="facebook_link_preflight.py",
            evidence=[CallerEvidence(
                caller_id="make:9530582:scheduled",
                caller_kind="make_scenario",
                target_scenario_id=9530582,
                target_runtime="facebook_link_preflight.py",
                environment="TEST",
                active=False,
                evidence_ref="make://scenario/9530582",
            )],
        )
        self.assertTrue(result.complete)
        self.assertEqual((), result.blockers)

    def test_missing_evidence_fails_closed(self):
        result = build_caller_map(
            scenario_id=9528450,
            expected_runtime="facebook_text_direct_preflight.py",
            evidence=[],
        )
        self.assertFalse(result.complete)
        self.assertIn("NO_CALLER_EVIDENCE", result.blockers)

    def test_runtime_mismatch_blocks(self):
        result = build_caller_map(
            scenario_id=9532848,
            expected_runtime="facebook_video_short_preflight.py",
            evidence=[CallerEvidence(
                caller_id="legacy",
                caller_kind="make_scenario",
                target_scenario_id=9532848,
                target_runtime="wrong.py",
                environment="TEST",
                active=False,
                evidence_ref="evidence",
            )],
        )
        self.assertFalse(result.complete)
        self.assertIn("RUNTIME_TARGET_MISMATCH", result.blockers)

    def test_cutover_requires_all_gates(self):
        self.assertTrue(can_cut_over_caller(
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            external_action_safe=True,
        ))
        self.assertFalse(can_cut_over_caller(
            caller_map_complete=True,
            replay_parity_green=False,
            rollback_proven=True,
            external_action_safe=True,
        ))


if __name__ == "__main__":
    unittest.main()

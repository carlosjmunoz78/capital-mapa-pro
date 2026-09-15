import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.shadow_replay import (
    run_fail_closed_shadow_probe,
    run_shadow_replay_suite,
    shadow_replay_green,
)


class AdvisoryShadowReplayTests(unittest.TestCase):
    def test_replays_are_deterministic_and_green(self):
        results = run_shadow_replay_suite()
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertEqual(result.expected_status, "GREEN")
            self.assertEqual(result.actual_status, "GREEN")
            self.assertTrue(result.deterministic_match)
            self.assertTrue(result.audit_refs)

    def test_missing_evidence_fails_closed(self):
        self.assertEqual(run_fail_closed_shadow_probe(), "BLOCKED")

    def test_shadow_replay_gate_green(self):
        self.assertTrue(shadow_replay_green())


if __name__ == "__main__":
    unittest.main()

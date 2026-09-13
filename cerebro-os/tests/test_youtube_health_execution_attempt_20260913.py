import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class YouTubeHealthExecutionAttemptTest(unittest.TestCase):
    def test_youtube_health_remains_fail_closed_without_retained_execution(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "youtube_health_execution_attempt_20260913.py"))
        row = mod["assess"]()
        self.assertTrue(row["read_only_contract"])
        self.assertTrue(row["connection_ok"])
        self.assertTrue(row["activation_attempted"])
        self.assertTrue(row["manual_run_blocked_by_tool_controls"])
        self.assertFalse(row["retained_execution_proven"])
        self.assertTrue(row["scenario_inactive_after_attempt"])
        self.assertFalse(row["observability_youtube_green"])
        self.assertFalse(row["automatic_absence_policy_approval"])


if __name__ == "__main__":
    unittest.main()

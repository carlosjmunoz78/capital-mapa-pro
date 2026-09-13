import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LinkedInHealthRetainedExecutionTest(unittest.TestCase):
    def test_linkedin_retained_health_is_green_but_social_not_complete(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "linkedin_health_retained_execution_20260913.py"))
        row = mod["assess"]()
        self.assertTrue(row["connection_ok"])
        self.assertTrue(row["read_only_health_contract"])
        self.assertTrue(row["retained_execution_present"])
        self.assertTrue(row["retained_execution_success"])
        self.assertTrue(row["linkedin_retained_metric_evidence_green"])
        self.assertFalse(row["publishing_authorized"])
        self.assertFalse(row["youtube_retained_metric_evidence_green"])
        self.assertFalse(row["social_observability_complete"])


if __name__ == "__main__":
    unittest.main()

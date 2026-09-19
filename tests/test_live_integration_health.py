import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"cerebro-os"))

from observability.live_integration_health import assess_live_snapshot


class LiveIntegrationHealthTests(unittest.TestCase):
    def test_current_live_snapshot_is_partial_only_for_youtube(self):
        summary=assess_live_snapshot(ROOT/"cerebro-os/evidence/LIVE_INTEGRATION_HEALTH_2026-09-19.json")
        self.assertEqual(summary.crm_status,"GREEN")
        self.assertEqual(summary.gsc_status,"GREEN")
        self.assertEqual(summary.social_status,"GREEN")
        self.assertEqual(summary.youtube_status,"BLOCKED")
        self.assertEqual(summary.overall_status,"PARTIAL")
        self.assertEqual(summary.blockers,("YOUTUBE_CONNECTION_VALIDATION",))


if __name__=="__main__": unittest.main()

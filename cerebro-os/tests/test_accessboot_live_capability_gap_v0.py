import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jobs.assess_accessboot_capability_snapshot import assess_snapshot


class AccessbootLiveCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 22, 11, 5, tzinfo=timezone.utc)
        self.command = {
            "company_id": "fenix", "device_id": "pc-lab", "environment": "LAB",
            "version": "v0", "state": "COMPLETED", "semantic_verified": True,
            "completed_at": (self.now - timedelta(seconds=5)).isoformat(),
            "result": {
                "company_id": "fenix", "device_id": "pc-lab", "environment": "LAB",
                "version": "v0", "status": "COMPLETED",
                "evidence_ref": "ACCESSBOOT_CAPABILITY_SNAPSHOT",
                "local_service_version": "1.4.1",
                "paired": True, "extension_connected": True, "extension_fresh": True,
                "transport_online": True, "kill_switch_enabled": True,
                "browser_discovery_status": "GREEN",
                "chrome_profiles": [{"directory": "Default", "display_name": "private"}],
                "secret_value_included": False, "external_mutation_performed": False,
            }
        }

    def assess(self):
        return assess_snapshot(
            self.command, company_id="fenix", device_id="pc-lab", now=self.now)

    def test_verified_snapshot_is_metadata_only(self):
        result = self.assess()
        self.assertEqual(result["status"], "GREEN")
        self.assertEqual(result["profile_count"], 1)
        self.assertNotIn("private", str(result))
        self.assertEqual(result["generic_navigation"], "NOT_IMPLEMENTED")
        self.assertFalse(result["prod_activation_allowed"])

    def test_old_snapshot_requires_refresh(self):
        self.command["completed_at"] = (
            self.now - timedelta(seconds=301)).isoformat()
        self.assertEqual(self.assess()["status"], "PARTIAL")

    def test_cross_company_denied(self):
        self.command["result"]["company_id"] = "other"
        with self.assertRaises(PermissionError):
            self.assess()

    def test_false_readiness_blocks(self):
        self.command["result"]["extension_fresh"] = False
        self.assertEqual(self.assess()["status"], "PARTIAL")

    def test_secret_indicator_is_security_incident(self):
        self.command["result"]["secret_value_included"] = True
        result = self.assess()
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_reason"], "SECURITY_INCIDENT")

    def test_external_mutation_flag_blocks(self):
        self.command["result"]["external_mutation_performed"] = True
        self.assertEqual(self.assess()["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()

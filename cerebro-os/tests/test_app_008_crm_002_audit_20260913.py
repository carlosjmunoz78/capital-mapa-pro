import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class App008Crm002AuditTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_008_crm_002_audit_20260913.py"))

    def test_reports_backend_is_green_without_overclaiming_ui(self):
        result = self.mod["assess"]()
        audit = self.mod["AUDIT"]["APP_008_reports"]
        self.assertTrue(result["APP_008_backend_green"])
        self.assertFalse(result["APP_008_ui_green"])
        self.assertTrue(audit["daily_snapshot_rls"])
        self.assertTrue(audit["weekly_snapshot_rls"])
        self.assertFalse(audit["send_or_export_mutation_proven"])

    def test_legacy_crm_sync_is_retired_and_fail_closed(self):
        result = self.mod["assess"]()
        audit = self.mod["AUDIT"]["CRM_002_sync"]
        self.assertTrue(result["CRM_002_legacy_sync_retirement_green"])
        self.assertFalse(result["safe_to_run_legacy_sync"])
        self.assertEqual(audit["retirement_error"], "migration_endpoint_retired")
        self.assertFalse(audit["legacy_sync_execution_allowed"])
        self.assertFalse(audit["matching_db_rpc_names_present"])


if __name__ == "__main__":
    unittest.main()

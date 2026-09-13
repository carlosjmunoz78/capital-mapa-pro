import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppCrmRbacAuditTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_crm_rbac_audit_20260913.py"))

    def test_rbac_navigation_is_live_and_fail_closed(self):
        result = self.mod["assess"]()
        self.assertTrue(result["APP_002_RBAC_navigation_green"])
        self.assertEqual(result["role_count"], 3)
        self.assertEqual(result["status"], "APP_002_RBAC_NAVIGATION_GREEN")

    def test_unknown_roles_get_no_navigation_and_no_prod_write_was_used(self):
        rbac = self.mod["RBAC"]
        self.assertEqual(rbac["unknown_role_navigation"], ())
        self.assertFalse(rbac["prod_write_performed"])
        self.assertTrue(rbac["active_actor_required"])


if __name__ == "__main__":
    unittest.main()

import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppCrmModuleContractAuditTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_crm_module_contract_audit_20260913.py"))

    def test_structural_server_contracts_are_green_without_prod_write(self):
        result = self.mod["assess"]()
        self.assertTrue(result["all_structural_contracts_green"])
        self.assertFalse(result["prod_write_performed"])
        self.assertEqual(len(result["structural_contract_green"]), 7)

    def test_runtime_gaps_remain_fail_closed(self):
        result = self.mod["assess"]()
        self.assertFalse(result["APP_004_runtime_migration_complete"])
        self.assertFalse(result["APP_006_create_contract_complete"])


if __name__ == "__main__":
    unittest.main()

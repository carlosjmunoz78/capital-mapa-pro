import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "runtime" / "supabase_recovery_target_inventory_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_recovery_target_inventory_20260913", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SupabaseRecoveryTargetInventoryTests(unittest.TestCase):
    def test_existing_resources_do_not_fake_restore_target(self):
        a = module.assess()
        self.assertEqual(a["project_count"], 2)
        self.assertEqual(a["safe_existing_restore_target_count"], 0)
        self.assertEqual(a["non_default_branch_count"], 0)
        self.assertFalse(a["isolated_restore_target_available_now"])

    def test_no_paid_resource_or_prod_restore_is_created_by_inventory(self):
        a = module.assess()
        self.assertFalse(a["new_paid_resource_created"])
        self.assertFalse(a["automatic_prod_restore_allowed"])
        self.assertFalse(a["provider_restore_green"])


if __name__ == "__main__":
    unittest.main()

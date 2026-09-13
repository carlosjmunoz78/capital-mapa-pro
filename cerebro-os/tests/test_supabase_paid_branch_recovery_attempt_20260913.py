import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "runtime" / "supabase_paid_branch_recovery_attempt_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_paid_branch_recovery_attempt_20260913", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SupabasePaidBranchRecoveryAttemptTests(unittest.TestCase):
    def test_failed_branch_is_not_counted_as_restore_or_security_replay(self):
        result = module.assess()
        self.assertTrue(result["attempted_isolated_branch"])
        self.assertTrue(result["provider_migration_failed"])
        self.assertFalse(result["usable_restore_target"])
        self.assertFalse(result["real_prod_data_restore_proven"])
        self.assertFalse(result["real_security_db_replay_proven"])

    def test_cleanup_stops_cost_and_preserves_existing_systems(self):
        result = module.assess()
        self.assertTrue(result["cost_stopped_after_failure"])
        self.assertTrue(result["prod_preserved"])
        self.assertTrue(result["legacy_preserved"])
        self.assertEqual(result["status"], "PAID_BRANCH_ATTEMPT_FAILED_CLEANED_UP_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()

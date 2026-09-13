import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "runtime" / "supabase_security_live_behavior_fingerprint_20260913.py"
spec = importlib.util.spec_from_file_location("behavior_snapshot", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BehaviorSnapshotTests(unittest.TestCase):
    def test_snapshot(self):
        result = module.assess_behavior_fingerprint()
        self.assertEqual(result["rpc_count"], 15)
        self.assertTrue(result["all_use_auth_uid"])
        self.assertTrue(result["all_build_jsonb"])
        self.assertFalse(result["any_delete_observed"])
        self.assertTrue(result["old_behavior_baseline_ready"])
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["security_green"])
        self.assertEqual(len(result["expected_version_mutators"]), 2)
        self.assertEqual(len(result["idempotent_mutators"]), 2)
        self.assertEqual(len(result["activity_log_mutators"]), 2)
        self.assertEqual(len(result["notification_mutators"]), 1)


if __name__ == "__main__":
    unittest.main()

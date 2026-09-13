import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_live_rpc_snapshot_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_security_live_rpc_snapshot_20260913", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityLiveRpcSnapshotTests(unittest.TestCase):
    def test_live_metadata_baseline_is_complete_and_fail_closed(self):
        result = module.assess_live_rpc_snapshot()
        self.assertEqual(result["rpc_count"], 15)
        self.assertTrue(result["all_15_present_live"])
        self.assertTrue(result["all_15_security_definer_live"])
        self.assertTrue(result["all_15_authenticated_execute_live"])
        self.assertTrue(result["parity_baseline_ready"])
        self.assertFalse(result["prod_mutation_performed"])
        self.assertFalse(result["grant_or_rls_change_performed"])
        self.assertFalse(result["retirement_performed"])
        self.assertFalse(result["security_green"])
        self.assertEqual(len(result["aggregate_contract_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()

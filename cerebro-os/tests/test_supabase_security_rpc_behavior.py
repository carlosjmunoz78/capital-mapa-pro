import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_rpc_behavior.py"
spec = importlib.util.spec_from_file_location("supabase_security_rpc_behavior", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabaseSecurityRpcBehaviorTests(unittest.TestCase):
    def test_surface_is_exactly_24_unique_rpcs(self):
        result = module.assess_rpc_behavior_surface()
        self.assertEqual(result["rpc_count"], 24)
        self.assertEqual(result["read_only_count"], 9)
        self.assertEqual(result["mutating_count"], 15)
        self.assertTrue(result["unique"])

    def test_remediation_is_fail_closed(self):
        result = module.assess_rpc_behavior_surface()
        self.assertFalse(result["automatic_revoke_allowed"])
        self.assertFalse(result["automatic_security_invoker_conversion_allowed"])
        self.assertFalse(result["automatic_prod_mutation_allowed"])
        self.assertTrue(result["mutator_parity_required_before_change"])
        self.assertEqual(result["human_reason"], "HIGH_RISK")

    def test_read_and_mutating_sets_do_not_overlap(self):
        self.assertTrue(set(module.READ_ONLY_RPCS).isdisjoint(module.MUTATING_RPCS))


if __name__ == "__main__":
    unittest.main()

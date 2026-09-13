import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "runtime" / "supabase_security_live_acl_snapshot_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_security_live_acl_snapshot_20260913", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SupabaseSecurityLiveAclSnapshotTests(unittest.TestCase):
    def test_exact_live_mutator_count_and_acl_baseline(self):
        assessment = module.assess_snapshot()
        self.assertEqual(assessment["mutator_count"], 15)
        self.assertTrue(assessment["all_security_definer"])
        self.assertTrue(assessment["all_have_definition_fingerprint"])
        self.assertTrue(assessment["authenticated_execute_observed"])

    def test_snapshot_never_authorizes_prod_security_change(self):
        assessment = module.assess_snapshot()
        self.assertFalse(assessment["prod_security_change_allowed"])
        self.assertEqual(module.SNAPSHOT["human_gate_for_security_change"], "HIGH_RISK")
        self.assertFalse(module.SNAPSHOT["grant_or_rls_change_allowed"])
        self.assertFalse(module.SNAPSHOT["retirement_allowed"])


if __name__ == "__main__":
    unittest.main()

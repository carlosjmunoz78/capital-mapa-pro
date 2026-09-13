import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "runtime" / "supabase_security_wrapper_candidate_snapshot_20260913.py"
spec = importlib.util.spec_from_file_location("supabase_security_wrapper_candidate_snapshot_20260913", PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class SupabaseSecurityWrapperCandidateSnapshotTests(unittest.TestCase):
    def test_exact_candidate_inventory(self):
        a = module.assess()
        self.assertEqual(a["target_count"], 15)
        self.assertEqual(a["direct_server_wrapper_candidate_count"], 3)
        self.assertEqual(a["without_direct_name_matched_wrapper_count"], 12)
        self.assertEqual(set(a["candidates"].values()), {
            "fenix_prod_chat_send_server",
            "fenix_prod_exp_update_server",
            "fenix_prod_profile_update_server",
        })

    def test_candidate_presence_is_not_parity_proof(self):
        a = module.assess()
        self.assertEqual(a["parity_proven_count"], 0)
        self.assertFalse(a["automatic_prod_change_allowed"])
        self.assertEqual(len(module.PARITY_DIMENSIONS), 8)


if __name__ == "__main__":
    unittest.main()

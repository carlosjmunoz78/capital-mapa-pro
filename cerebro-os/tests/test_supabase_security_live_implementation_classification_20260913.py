import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_live_implementation_classification_20260913.py"
spec = importlib.util.spec_from_file_location("live_impl", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LiveImplementationClassificationTests(unittest.TestCase):
    def test_fail_closed_classification(self):
        result = module.assess()
        self.assertEqual(result["target_count"], 15)
        self.assertEqual(result["direct_delegation_count"], 2)
        self.assertEqual(result["distinct_implementation_count"], 1)
        self.assertEqual(result["without_identified_server_equivalent_count"], 12)
        self.assertFalse(result["automatic_prod_mutation_allowed"])
        self.assertFalse(result["grant_revoke_allowed"])
        self.assertFalse(result["retirement_allowed"])
        self.assertFalse(result["security_green"])
        self.assertIn("fenix_prod_chat_send_user", result["direct_delegations"])
        self.assertIn("fenix_prod_exp_update", result["direct_delegations"])
        self.assertIn("fenix_prod_profile_update_user", result["distinct_implementations"])
        self.assertEqual(module.TARGETS["fenix_prod_sign_create"]["parity_status"], "SIGNATURE_REQUIRED_AND_SERVER_EQUIVALENT_NOT_IDENTIFIED")


if __name__ == "__main__":
    unittest.main()

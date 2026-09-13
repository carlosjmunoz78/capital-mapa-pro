import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_wrapper_contracts_20260913.py"
spec = importlib.util.spec_from_file_location("wrapper_contracts", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WrapperContractTests(unittest.TestCase):
    def test_contracts_are_complete_and_fail_closed(self):
        result = module.assess()
        self.assertEqual(result["contract_count"], 13)
        self.assertTrue(result["all_have_actor_context"])
        self.assertTrue(result["all_have_preservation_contract"])
        self.assertTrue(result["profile_existing_server_reuse_forbidden"])
        self.assertTrue(result["signature_required_preserved"])
        self.assertFalse(result["prod_function_created"])
        self.assertFalse(result["prod_function_replaced"])
        self.assertFalse(result["automatic_prod_mutation_allowed"])
        self.assertEqual(
            module.WRAPPER_CONTRACTS["fenix_prod_profile_update_user"]["proposed_server"],
            "fenix_prod_profile_update_self_server",
        )


if __name__ == "__main__":
    unittest.main()

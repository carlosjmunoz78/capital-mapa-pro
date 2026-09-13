import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_parity_matrix_20260913.py"
spec = importlib.util.spec_from_file_location("security_parity", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SecurityParityMatrixTests(unittest.TestCase):
    def test_fail_closed_parity_matrix(self):
        result = module.assess()
        self.assertEqual(result["target_count"], 15)
        self.assertEqual(result["parity_dimension_count"], 8)
        self.assertEqual(result["fully_green_count"], 0)
        self.assertEqual(result["structural_7_of_8_count"], 2)
        self.assertEqual(result["wrapper_required_count"], 12)
        self.assertTrue(result["signature_required_preserved"])
        self.assertFalse(result["automatic_prod_mutation_allowed"])
        self.assertFalse(result["grant_revoke_allowed"])
        self.assertFalse(result["retirement_allowed"])
        self.assertFalse(result["security_green"])
        self.assertEqual(
            module.TARGETS["fenix_prod_profile_update_user"]["status"],
            "NOT_EQUIVALENT_BY_INSPECTION",
        )
        for name in ("fenix_prod_chat_send_user", "fenix_prod_exp_update"):
            dims = module.TARGETS[name]["dimensions"]
            self.assertEqual(sum(dims.values()), 7)
            self.assertFalse(dims["rollback_path_proven"])


if __name__ == "__main__":
    unittest.main()

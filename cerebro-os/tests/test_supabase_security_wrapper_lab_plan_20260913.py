import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_wrapper_lab_plan_20260913.py"
spec = importlib.util.spec_from_file_location("wrapper_lab_plan", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class WrapperLabPlanTests(unittest.TestCase):
    def test_plan_is_complete_ordered_and_fail_closed(self):
        result = module.assess()
        queue = module.build_lab_queue()
        self.assertEqual(result["plan_count"], 13)
        self.assertEqual(result["unique_legacy_count"], 13)
        self.assertEqual(result["unique_server_count"], 13)
        self.assertTrue(result["all_have_nine_required_checks"])
        self.assertTrue(result["signature_required_preserved"])
        self.assertFalse(result["prod_apply_allowed"])
        self.assertFalse(result["prod_grant_change_allowed"])
        self.assertFalse(result["legacy_retirement_allowed"])
        self.assertFalse(result["lab_implementation_green"])
        self.assertEqual([row["order"] for row in queue], list(range(1, 14)))
        self.assertEqual(queue[-1]["human_required"], "SIGNATURE_REQUIRED")


if __name__ == "__main__":
    unittest.main()

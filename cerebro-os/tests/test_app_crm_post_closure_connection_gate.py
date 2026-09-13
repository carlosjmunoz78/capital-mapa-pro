import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "app_crm_post_closure_connection_gate.py"
spec = importlib.util.spec_from_file_location("app_crm_post_closure_connection_gate", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AppCrmPostClosureConnectionGateTests(unittest.TestCase):
    def test_connection_is_blocked_while_any_global_gap_is_red(self):
        status = {name: True for name in module.REQUIRED_GLOBAL_GAPS}
        status[module.REQUIRED_GLOBAL_GAPS[0]] = False
        result = module.assess_app_crm_connection(status)
        self.assertFalse(result["app_crm_connection_allowed"])
        self.assertFalse(result["app_preprod_reactivated"])
        self.assertEqual(result["status"], "APP_CRM_CONNECTION_BLOCKED_UNTIL_GLOBAL_CLOSURE")

    def test_connection_can_only_become_ready_after_all_five_gaps_are_green(self):
        status = {name: True for name in module.REQUIRED_GLOBAL_GAPS}
        result = module.assess_app_crm_connection(status)
        self.assertTrue(result["global_closure_green"])
        self.assertTrue(result["app_crm_connection_allowed"])
        self.assertTrue(result["gateway_required"])
        self.assertFalse(result["direct_model_connection_allowed"])
        self.assertFalse(result["direct_uncontrolled_table_write_allowed"])
        self.assertFalse(result["app_preprod_reactivated"])
        self.assertFalse(result["prod_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()

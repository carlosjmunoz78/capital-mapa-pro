import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AppRpcLiveParityReadonlyTests(unittest.TestCase):
    def setUp(self):
        self.mod = runpy.run_path(str(ROOT / "runtime" / "app_rpc_live_parity_readonly_20260913.py"))

    def test_safe_live_parity_is_exact(self):
        result = self.mod["assess"]()
        self.assertEqual(result["checks"], 8)
        self.assertTrue(result["all_exact_equal"])
        self.assertTrue(result["all_non_mutating"])

    def test_write_and_gateway_gates_remain_closed(self):
        result = self.mod["assess"]()
        self.assertFalse(result["successful_write_path_parity_proven"])
        self.assertFalse(result["gateway_end_to_end_parity_proven"])
        self.assertFalse(result["authenticated_execute_revoke_allowed"])


if __name__ == "__main__":
    unittest.main()

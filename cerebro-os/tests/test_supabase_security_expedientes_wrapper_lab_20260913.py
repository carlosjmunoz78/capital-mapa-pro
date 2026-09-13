import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_security_expedientes_wrapper_lab_20260913.py"
spec = importlib.util.spec_from_file_location("expedientes_wrapper_lab", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ExpedientesWrapperLabTests(unittest.TestCase):
    def test_exp_create_semantic_replay_is_green_in_lab_only(self):
        result = module.replay()
        self.assertEqual(result["fixture_count"], 6)
        self.assertTrue(result["lab_semantic_replay_green"])
        self.assertTrue(result["write_set_replay_pending"])
        self.assertFalse(result["rollback_path_proven"])
        self.assertFalse(result["prod_parity_green"])
        self.assertFalse(result["prod_mutation_allowed"])
        self.assertFalse(result["grant_change_allowed"])
        self.assertFalse(result["legacy_retirement_allowed"])


if __name__ == "__main__":
    unittest.main()

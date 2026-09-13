import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "zero_cost_recovery_rehearsal.py"
spec = importlib.util.spec_from_file_location("zero_cost_recovery_rehearsal", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ZeroCostRecoveryRehearsalTests(unittest.TestCase):
    def test_backup_restore_integrity_smoke_and_cleanup_are_green(self):
        result = module.rehearse_zero_cost_restore(
            {
                "registry/engine.json": b'{"engine_id":"FACT-001","version":"v0"}',
                "config/policy.txt": b"fail_closed=true\n",
            }
        )
        self.assertEqual(result["mode"], "ZERO_COST_LOCAL_CI_ISOLATED")
        self.assertEqual(result["source_files"], 2)
        self.assertTrue(result["backup_integrity"])
        self.assertTrue(result["restore_integrity"])
        self.assertTrue(result["application_smoke"]["ok"])
        self.assertEqual(result["application_smoke"]["json_files"], 1)
        self.assertTrue(result["cleanup_ok"])
        self.assertFalse(result["provider_restore_proven"])
        self.assertFalse(result["prod_mutated"])
        self.assertFalse(result["secrets_required"])
        self.assertEqual(result["additional_cost_eur"], 0)

    def test_empty_source_fails_closed(self):
        with self.assertRaises(ValueError):
            module.rehearse_zero_cost_restore({})

    def test_path_traversal_fails_closed(self):
        with self.assertRaises(ValueError):
            module.rehearse_zero_cost_restore({"../escape.txt": b"no"})


if __name__ == "__main__":
    unittest.main()

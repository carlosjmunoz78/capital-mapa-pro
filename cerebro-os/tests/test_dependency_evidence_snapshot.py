import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "dependency_evidence_snapshot.py"
spec = importlib.util.spec_from_file_location("dependency_evidence_snapshot", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DependencyEvidenceSnapshotTests(unittest.TestCase):
    def test_required_systems_are_all_present(self):
        self.assertEqual(
            set(module.SYSTEM_STATUS),
            {"app", "crm", "supabase", "notion", "wordpress", "seo"},
        )

    def test_historical_inventory_does_not_become_live_green(self):
        result = module.assess_dependency_snapshot()
        self.assertTrue(result["inventory_complete"])
        self.assertTrue(result["historical_contracts_complete"])
        self.assertEqual(set(result["live_unverified"]), {"app", "crm", "supabase", "notion", "wordpress"})
        self.assertFalse(result["dependency_green"])
        self.assertFalse(result["prod_candidate_allowed"])

    def test_old_systems_are_preserved(self):
        result = module.assess_dependency_snapshot()
        self.assertFalse(result["old_systems_may_be_deleted"])
        self.assertTrue(result["parallel_migration_required"])
        self.assertEqual(result["migration_rule"], "CONSERVAR_ENTENDER_ENVOLVER_PROBAR_MEJORAR_MIGRAR")


if __name__ == "__main__":
    unittest.main()

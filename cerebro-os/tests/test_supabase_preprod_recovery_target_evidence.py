import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "supabase_preprod_recovery_target_evidence.py"
spec = importlib.util.spec_from_file_location("supabase_preprod_recovery_target_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SupabasePreprodRecoveryTargetEvidenceTests(unittest.TestCase):
    def test_metadata_supports_preprod_surface_but_legacy_core_is_preserved(self):
        result = module.assess_recovery_target()
        self.assertTrue(result["metadata_supports_preprod_classification"])
        self.assertEqual(
            result["role"],
            "EXISTING_NON_PROD_PREPROD_TEST_SURFACE_WITH_LEGACY_CORE_DEPENDENCY",
        )
        self.assertTrue(result["legacy_core_dependency_observed"])
        self.assertFalse(result["dependency_noncriticality_proven"])

    def test_existing_project_is_rejected_as_destructive_restore_target(self):
        result = module.assess_recovery_target()
        self.assertTrue(result["destructive_restore_target_rejected"])
        self.assertFalse(result["existing_project_safe_for_destructive_restore"])
        self.assertFalse(result["destructive_action_allowed"])
        self.assertFalse(result["prod_mutation_allowed"])
        self.assertFalse(result["restore_executed"])
        self.assertFalse(result["safe_restore_target_proven"])
        self.assertFalse(result["provider_restore_green"])

    def test_provider_restore_requires_isolated_restore_or_clone(self):
        result = module.assess_recovery_target()
        self.assertEqual(
            set(result["required_restore_target_types"]),
            {"ISOLATED_RESTORE", "PREPROD_CLONE"},
        )
        self.assertTrue(result["isolated_restore_plan_proven"])
        self.assertTrue(result["integrity_and_smoke_plan_proven"])
        self.assertEqual(len(result["next_required_evidence"]), 6)
        self.assertEqual(
            result["status"],
            "PREPROD_SURFACE_CONFIRMED_LEGACY_CORE_PRESERVE_ISOLATED_CLONE_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()

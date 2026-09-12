import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from core_runtime_migration_coverage import COVERAGE, coverage_report


class CoreRuntimeMigrationCoverageTests(unittest.TestCase):
    def targets(self):
        return {item.runtime_target for item in COVERAGE}

    def test_all_declared_targets_present_is_green_but_not_prod_cutover(self):
        out = coverage_report(
            company_id="fenix",
            environment="LAB",
            version="1.0.0",
            existing_targets=self.targets(),
        )
        self.assertEqual(out["status"], "GREEN_CODE_CI")
        self.assertTrue(out["all_targets_present"])
        self.assertTrue(out["old_preserved"])
        self.assertFalse(out["prod_cutover_allowed"])
        self.assertTrue(all(not row["external_mutation_allowed"] for row in out["rows"]))
        self.assertTrue(all(not row["delete_old_allowed"] for row in out["rows"]))

    def test_missing_target_fails_closed(self):
        targets = self.targets()
        targets.remove("runtime/dispatcher.py")
        out = coverage_report(
            company_id="fenix",
            environment="PREPROD",
            version="1.0.0",
            existing_targets=targets,
        )
        self.assertEqual(out["status"], "MIGRATION_TARGETS_MISSING")
        self.assertFalse(out["all_targets_present"])
        self.assertIn("runtime/dispatcher.py", out["missing_targets"])

    def test_prod_verification_rejected(self):
        with self.assertRaises(ValueError):
            coverage_report(
                company_id="fenix",
                environment="PROD",
                version="1.0.0",
                existing_targets=self.targets(),
            )


if __name__ == "__main__":
    unittest.main()

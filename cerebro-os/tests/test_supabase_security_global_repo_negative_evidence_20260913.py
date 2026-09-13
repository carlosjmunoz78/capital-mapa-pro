import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityGlobalRepoNegativeEvidenceTest(unittest.TestCase):
    def test_expanded_inventory_stays_fail_closed(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "supabase_security_global_repo_negative_evidence_20260913.py"))
        row = mod["assess"]()
        self.assertEqual(row["repository_count"], 5)
        self.assertEqual(row["additional_repository_count"], 3)
        self.assertTrue(row["additional_repositories_zero_fenix_prod_prefix_matches"])
        self.assertEqual(row["app_known_direct_caller_count"], 6)
        self.assertEqual(row["app_remaining_mutators_zero_indexed_match_count"], 9)
        self.assertEqual(row["prod_edge_surfaces_read_only_inspected"], 33)
        self.assertFalse(row["global_absence_proven"])
        self.assertFalse(row["safe_retirement_proven"])
        self.assertFalse(row["caller_migration_complete"])
        self.assertFalse(row["prod_privilege_change_allowed"])
        self.assertFalse(row["automatic_prod_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()

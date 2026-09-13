import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityCallerClosureMatrixTest(unittest.TestCase):
    def test_internal_inventory_green_but_cutover_stays_closed(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "supabase_security_caller_closure_matrix_20260913.py"))
        row = mod["assess"]()
        self.assertTrue(row["known_app_direct_callers_preserved"])
        self.assertTrue(row["negative_searches_treated_as_non_proof_of_global_absence"])
        self.assertTrue(row["edge_inventory_complete_for_current_prod_project_snapshot"])
        self.assertTrue(row["repository_inventory_expanded"])
        self.assertTrue(row["make_negative_evidence_recorded"])
        self.assertTrue(row["caller_discovery_internal_inventory_green"])
        self.assertEqual(len(row["remaining_required"]), 4)
        self.assertFalse(row["safe_retirement_proven"])
        self.assertFalse(row["security_review_green"])
        self.assertFalse(row["prod_privilege_change_allowed"])
        self.assertFalse(row["automatic_prod_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()

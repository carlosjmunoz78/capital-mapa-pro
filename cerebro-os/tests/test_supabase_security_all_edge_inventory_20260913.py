import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityAllEdgeInventoryTest(unittest.TestCase):
    def test_all_current_edges_accounted_for_fail_closed(self):
        mod = runpy.run_path(str(ROOT / "runtime" / "supabase_security_all_edge_inventory_20260913.py"))
        row = mod["assess"]()
        self.assertEqual(row["total_prod_project_edge_surfaces"], 38)
        self.assertEqual(row["previously_inspected_security_edge_surfaces"], 33)
        self.assertEqual(row["newly_inspected_surface_count"], 5)
        self.assertEqual(row["newly_inspected_retired_410_count"], 4)
        self.assertTrue(row["all_current_edge_surfaces_now_accounted_for"])
        self.assertFalse(row["direct_client_mutator_retirement_authorized"])
        self.assertFalse(row["global_caller_absence_proven"])
        self.assertFalse(row["prod_edge_modified"])
        self.assertFalse(row["prod_privilege_change_allowed"])
        self.assertFalse(row["automatic_prod_mutation_allowed"])


if __name__ == "__main__":
    unittest.main()

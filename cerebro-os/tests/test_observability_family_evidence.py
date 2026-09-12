import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "observability_family_evidence.py"
spec = importlib.util.spec_from_file_location("observability_family_evidence", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ObservabilityFamilyEvidenceTests(unittest.TestCase):
    def test_expected_families_present(self):
        self.assertEqual(
            set(module.FAMILY_EVIDENCE),
            {"app_crm", "document_intelligence", "lead_ingest", "daily_reporting", "seo", "social", "engine_factory"},
        )

    def test_no_family_is_promoted_without_cost_measurement(self):
        result = module.assess_all_families()
        self.assertFalse(result["all_green"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertTrue(result["cost_measurement_pending"])
        for row in result["families"].values():
            self.assertFalse(row["prod_candidate_allowed"])
            self.assertIsNone(row["monthly_cost_eur"])
            self.assertFalse(row["money_limit_triggered"])

    def test_live_prod_surfaces_have_real_operational_refs_but_cost_pending(self):
        for family in ("app_crm", "document_intelligence", "lead_ingest", "daily_reporting"):
            row = module.assess_family(family)
            self.assertTrue(row["checks"]["logs"])
            self.assertTrue(row["checks"]["metrics"])
            self.assertTrue(row["checks"]["incidents"])
            self.assertFalse(row["checks"]["cost"])
            self.assertEqual(row["missing"], ("cost",))

    def test_partial_families_fail_closed(self):
        for family in ("seo", "social", "engine_factory"):
            row = module.assess_family(family)
            self.assertFalse(row["green"])
            self.assertTrue(row["missing"])


if __name__ == "__main__":
    unittest.main()

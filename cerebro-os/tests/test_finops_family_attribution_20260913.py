import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).parents[1] / "runtime" / "finops_family_attribution_20260913.py"
spec = importlib.util.spec_from_file_location("finops_family_attribution_20260913", PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FinopsFamilyAttributionTests(unittest.TestCase):
    def test_shared_provider_costs_are_not_arbitrarily_split(self):
        result = mod.assess()
        self.assertEqual(result["provider_count"], 6)
        self.assertEqual(result["family_count"], 7)
        self.assertFalse(result["arbitrary_allocation_performed"])
        self.assertFalse(result["estimated_amounts_used"])
        self.assertFalse(result["all_provider_amounts_known"])
        self.assertFalse(result["all_family_costs_attributed"])
        self.assertFalse(result["finops_green"])

    def test_unresolved_provider_evidence_stays_explicit(self):
        self.assertEqual(mod.PROVIDER_COST_EVIDENCE["google_cloud"]["monthly_amount"], None)
        self.assertEqual(mod.PROVIDER_COST_EVIDENCE["notion"]["monthly_amount"], None)
        self.assertEqual(mod.assess_family("seo")["unresolved_providers"], ("notion",))
        self.assertIn("google_cloud", mod.assess_family("document_intelligence")["unresolved_providers"])


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from seo_gsc_prod_contract import GscCaptureContract, assess_gsc_edge, inventory


class SeoGscProdContractTests(unittest.TestCase):
    def test_inventory_has_two_live_prod_edges(self):
        data = inventory()
        self.assertEqual(set(data), {9597710, 9550706})
        self.assertEqual(data[9597710]["dimensions"], ("PAGE",))
        self.assertEqual(data[9550706]["dimensions"], ("QUERY", "PAGE", "DEVICE", "COUNTRY"))

    def test_live_edge_is_preserved_not_migrated(self):
        out = assess_gsc_edge(
            GscCaptureContract(
                company_id="fenix-capital",
                engine_id="SEO-GSC",
                environment="PROD",
                version="1.0.0",
                scenario_id=9597710,
                site_url="https://fenixcapital.es/",
                window_days=30,
                dimensions=("PAGE",),
                mutates_notion_metrics_only=True,
                connection_ok=True,
            )
        )
        self.assertEqual(out["status"], "LIVE_EDGE_PRESERVE_GREEN")
        self.assertTrue(out["edge_preserved"])
        self.assertFalse(out["migration_required"])
        self.assertFalse(out["runtime_external_action_allowed"])
        self.assertFalse(out["runtime_notion_mutation_allowed"])

    def test_connection_failure_blocks(self):
        out = assess_gsc_edge(
            GscCaptureContract(
                company_id="fenix-capital",
                engine_id="SEO-GSC",
                environment="PROD",
                version="1.0.0",
                scenario_id=9550706,
                site_url="https://fenixcapital.es/",
                window_days=30,
                dimensions=("QUERY", "PAGE", "DEVICE", "COUNTRY"),
                mutates_notion_metrics_only=False,
                connection_ok=False,
            )
        )
        self.assertEqual(out["status"], "BLOCKED_LIVE_EDGE")
        self.assertIn("CONNECTION_NOT_OK", out["blockers"])

    def test_fixture_matches_live_contract(self):
        path = ROOT / "runtime" / "fixtures" / "seo_gsc_live_contract_2026-09-12.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(data["scenarios"]), 2)
        self.assertTrue(data["runtime_invariants"]["preserve_active_make_edge"])
        self.assertTrue(data["runtime_invariants"]["do_not_deactivate"])
        self.assertFalse(data["runtime_invariants"]["runtime_external_action_allowed"])


if __name__ == "__main__":
    unittest.main()

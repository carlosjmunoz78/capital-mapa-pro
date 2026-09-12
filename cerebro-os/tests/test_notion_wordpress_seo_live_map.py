import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "notion_wordpress_seo_live_map.py"
spec = importlib.util.spec_from_file_location("notion_wordpress_seo_live_map", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NotionWordPressSeoLiveMapTests(unittest.TestCase):
    def test_live_edges_are_verified_without_prod_write(self):
        result = module.assess_live_map()
        self.assertTrue(result["notion_live_verified"])
        self.assertTrue(result["wordpress_preprod_live_verified"])
        self.assertTrue(result["seo_preprod_executor_live_verified"])
        self.assertTrue(result["seo_prod_read_only_edges_verified"])
        self.assertFalse(result["prod_mutation_performed"])

    def test_old_notion_bridge_remains_fail_closed(self):
        result = module.assess_live_map()
        self.assertTrue(result["notion_old_bridge_fail_closed"])

    def test_wordpress_prod_publish_is_not_claimed(self):
        result = module.assess_live_map()
        self.assertFalse(result["wordpress_prod_publish_exercised"])
        self.assertFalse(result["prod_candidate_allowed"])
        self.assertEqual(result["status"], "LIVE_NOTION_WORDPRESS_SEO_MAP_VERIFIED_PROD_WRITE_GATED")

    def test_seo_executor_safety_contract(self):
        cfg = module.SEO["executor_preprod"]
        self.assertEqual(set(cfg["allowed_fields"]), {"title", "excerpt"})
        self.assertTrue(cfg["published_target_blocked"])
        self.assertTrue(cfg["dry_run_supported"])
        self.assertTrue(cfg["post_write_verification"])
        self.assertTrue(cfg["rollback_on_verification_failure"])


if __name__ == "__main__":
    unittest.main()

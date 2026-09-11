import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "factory"))

from factory import build_manifest, scaffold


class FactoryTests(unittest.TestCase):
    def test_manifest_contains_required_governance(self):
        manifest = build_manifest("FACT-TEST", "Factory Test")
        self.assertEqual(manifest["environment"], "LAB")
        self.assertEqual(manifest["status"], "DEFINED_NOT_BUILT")
        self.assertEqual(manifest["cost_budget"]["target_additional_eur"], 0)
        self.assertIn("LOW_CONFIDENCE", manifest["human_exception_codes"])
        self.assertIn("deny_cross_company_by_default", manifest["policies"])

    def test_scaffold_creates_standard_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = scaffold(Path(tmp), "QA-999", "QA Test")
            self.assertTrue((target / "manifest.json").exists())
            for directory in ["config","contracts","policies","events","jobs","api","tests","evaluation","observability","ops","docs","training"]:
                self.assertTrue((target / directory).is_dir())
            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["engine_id"], "QA-999")

    def test_duplicate_engine_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scaffold(root, "DUP-001", "Duplicate")
            with self.assertRaises(FileExistsError):
                scaffold(root, "DUP-001", "Duplicate")


if __name__ == "__main__":
    unittest.main()

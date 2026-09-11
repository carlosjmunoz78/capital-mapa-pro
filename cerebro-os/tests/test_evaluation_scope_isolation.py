import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("quality_evaluation_scope", ROOT / "quality/evaluation.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["quality_evaluation_scope"] = mod
spec.loader.exec_module(mod)


class EvaluationScopeIsolationTests(unittest.TestCase):
    def result(self, company="fenix", env="LAB", version="1.0.0"):
        return mod.EvaluationResult("E-1", .95, .8, ("evidence:1",), company, env, version)

    def test_single_scope_can_pass(self):
        self.assertTrue(mod.aggregate((self.result(),), company_id="fenix", environment="LAB", version="1.0.0"))

    def test_cross_company_cannot_false_green(self):
        self.assertFalse(mod.aggregate((self.result("fenix"), self.result("other"))))

    def test_cross_environment_cannot_false_green(self):
        self.assertFalse(mod.aggregate((self.result(env="LAB"), self.result(env="PROD"))))

    def test_cross_version_cannot_false_green(self):
        self.assertFalse(mod.aggregate((self.result(version="1.0.0"), self.result(version="2.0.0"))))

    def test_evidence_is_required(self):
        no_evidence = mod.EvaluationResult("E-1", .95, .8, (), "fenix", "LAB", "1.0.0")
        self.assertFalse(mod.aggregate((no_evidence,)))


if __name__ == "__main__":
    unittest.main()

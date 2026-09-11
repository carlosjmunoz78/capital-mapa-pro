import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("company_health_scope", ROOT / "multicompany/health.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["company_health_scope"] = mod
spec.loader.exec_module(mod)


class CompanyHealthScopeIsolationTests(unittest.TestCase):
    def test_green_requires_evidence_and_exact_scope(self):
        states = {"FACT-001":"GREEN"}
        refs = {"FACT-001":("e:test",)}
        no_scope = mod.company_health(company_id="fenix", required_engines=("FACT-001",), engine_states=states, evidence_refs=refs, environment="PROD", version="2.0.0")
        self.assertEqual("RED", no_scope["state"])
        exact = mod.company_health(
            company_id="fenix", required_engines=("FACT-001",), engine_states=states, evidence_refs=refs,
            environment="PROD", version="2.0.0",
            evidence_scopes={"FACT-001":{"company_id":"fenix","environment":"PROD","version":"2.0.0"}},
        )
        self.assertEqual("GREEN", exact["state"])

    def test_wrong_version_cannot_false_green(self):
        result = mod.company_health(
            company_id="fenix", required_engines=("FACT-001",), engine_states={"FACT-001":"GREEN"},
            evidence_refs={"FACT-001":("e:test",)}, environment="PROD", version="2.0.0",
            evidence_scopes={"FACT-001":{"company_id":"fenix","environment":"PROD","version":"1.0.0"}},
        )
        self.assertEqual("RED", result["state"])
        self.assertEqual(("FACT-001",), result["scope_mismatch"])


if __name__ == "__main__":
    unittest.main()

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("readiness_matrix_scope", ROOT / "registry/readiness_matrix.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["readiness_matrix_scope"] = mod
spec.loader.exec_module(mod)


class ReadinessMatrixVersionScopeTests(unittest.TestCase):
    def test_other_version_operational_record_cannot_green_target(self):
        records = (
            {"engine_id":"FACT-001","company_id":"fenix","environment":"PROD","version":"1.0.0","state":"CONFIRMED_OPERATIONAL","evidence_refs":("e:old",)},
            {"engine_id":"FACT-001","company_id":"fenix","environment":"PROD","version":"2.0.0","state":"BLOCKED","evidence_refs":("e:block",)},
        )
        matrix = mod.build_readiness_matrix(canonical_ids=("FACT-001",), live_records=records, company_id="fenix", environment="PROD", version="2.0.0")
        self.assertEqual("BLOCKED", matrix[0]["state"])
        self.assertEqual("2.0.0", matrix[0]["version"])

    def test_missing_exact_version_is_unknown(self):
        records = ({"engine_id":"FACT-001","company_id":"fenix","environment":"PROD","version":"1.0.0","state":"CONFIRMED_OPERATIONAL","evidence_refs":("e",)},)
        matrix = mod.build_readiness_matrix(canonical_ids=("FACT-001",), live_records=records, company_id="fenix", environment="PROD", version="2.0.0")
        self.assertEqual("UNKNOWN_REQUIRES_AUDIT", matrix[0]["state"])
        self.assertEqual(0, matrix[0]["record_count"])


if __name__ == "__main__":
    unittest.main()

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("system_gate_scope", ROOT / "registry/system_gate.py")
gate = importlib.util.module_from_spec(spec)
sys.modules["system_gate_scope"] = gate
spec.loader.exec_module(gate)
ids = tuple(json.loads((ROOT / "registry/canonical_177.json").read_text(encoding="utf-8")))


class SystemGateVersionScopeTests(unittest.TestCase):
    def matrix(self, version="2.0.0"):
        return tuple({"engine_id": e, "company_id":"fenix", "environment":"PROD", "version":version, "state":"CONFIRMED_OPERATIONAL"} for e in ids)

    def test_exact_scope_can_be_green(self):
        result = gate.system_readiness(canonical_ids=ids, matrix=self.matrix(), environment="PROD", company_id="fenix", version="2.0.0")
        self.assertEqual("GREEN", result["state"])
        self.assertEqual(177, result["green_count"])

    def test_other_version_cannot_green_target(self):
        result = gate.system_readiness(canonical_ids=ids, matrix=self.matrix("1.0.0"), environment="PROD", company_id="fenix", version="2.0.0")
        self.assertEqual("RED", result["state"])
        self.assertTrue(result["scope_errors"])


if __name__ == "__main__":
    unittest.main()

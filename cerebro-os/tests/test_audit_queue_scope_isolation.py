import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_queue_scope", ROOT / "registry/audit_queue.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["audit_queue_scope"] = mod
spec.loader.exec_module(mod)


class AuditQueueScopeIsolationTests(unittest.TestCase):
    def test_operational_other_version_cannot_close_target(self):
        matrix = ({"engine_id":"FACT-001","company_id":"fenix","environment":"PROD","version":"1.0.0","state":"CONFIRMED_OPERATIONAL"},)
        queue = mod.build_audit_queue(matrix, target_environment="PROD", company_id="fenix", target_version="2.0.0")
        self.assertEqual(1, len(queue))
        self.assertEqual("VERSION_SCOPE_MISMATCH", queue[0]["reason"])

    def test_exact_operational_scope_closes_target(self):
        matrix = ({"engine_id":"FACT-001","company_id":"fenix","environment":"PROD","version":"2.0.0","state":"CONFIRMED_OPERATIONAL"},)
        self.assertEqual((), mod.build_audit_queue(matrix, target_environment="PROD", company_id="fenix", target_version="2.0.0"))

    def test_lab_green_stays_promotion_required_for_prod(self):
        matrix = ({"engine_id":"FACT-001","company_id":"fenix","environment":"LAB","version":"2.0.0","state":"LAB_GREEN"},)
        queue = mod.build_audit_queue(matrix, target_environment="PROD", company_id="fenix", target_version="2.0.0")
        self.assertEqual("PROMOTION_REQUIRED", queue[0]["reason"])


if __name__ == "__main__":
    unittest.main()

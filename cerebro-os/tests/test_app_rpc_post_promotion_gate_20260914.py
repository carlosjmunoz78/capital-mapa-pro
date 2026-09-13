from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "app_rpc_post_promotion_gate_20260914.py"
spec = importlib.util.spec_from_file_location("app_rpc_post_promotion_gate_20260914", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class AppRpcPostPromotionGateTests(unittest.TestCase):
    def setUp(self):
        self.original = dict(mod.EVIDENCE)

    def tearDown(self):
        mod.EVIDENCE.clear()
        mod.EVIDENCE.update(self.original)

    def test_source_promotion_is_green_but_security_is_still_fail_closed(self):
        row = mod.assess()
        self.assertTrue(row["source_promotion_green"])
        self.assertFalse(row["authenticated_http_e2e_proven"])
        self.assertFalse(row["http_write_path_rollback_proven"])
        self.assertFalse(row["legacy_retirement_allowed"])
        self.assertFalse(row["legacy_retirement_applied"])
        self.assertFalse(row["security_green"])
        self.assertEqual(row["status"], "SOURCE_PROMOTION_GREEN_HTTP_AUTH_E2E_OPEN")

    def test_retirement_cannot_be_allowed_by_source_provenance_alone(self):
        mod.EVIDENCE["authenticated_http_e2e_proven"] = True
        mod.EVIDENCE["http_write_path_rollback_proven"] = False
        self.assertFalse(mod.assess()["legacy_retirement_allowed"])

        mod.EVIDENCE["authenticated_http_e2e_proven"] = False
        mod.EVIDENCE["http_write_path_rollback_proven"] = True
        self.assertFalse(mod.assess()["legacy_retirement_allowed"])

    def test_cloudflare_parallel_failure_cannot_be_silently_promoted(self):
        mod.EVIDENCE["authenticated_http_e2e_proven"] = True
        mod.EVIDENCE["http_write_path_rollback_proven"] = True
        mod.EVIDENCE["legacy_retirement_applied"] = True
        mod.EVIDENCE["cloudflare_pages_parallel_check_green"] = False
        mod.EVIDENCE["cloudflare_pages_routing_role_proven"] = False
        row = mod.assess()
        self.assertFalse(row["cloudflare_topology_closed"])
        self.assertFalse(row["security_green"])


if __name__ == "__main__":
    unittest.main()

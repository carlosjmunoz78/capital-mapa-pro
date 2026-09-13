from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "human_required_blocker_registry_20260914.py"
spec = importlib.util.spec_from_file_location("human_required_blocker_registry_20260914", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


class HumanRequiredBlockerRegistryTests(unittest.TestCase):
    def test_registry_is_canonical_unique_and_fail_closed(self):
        row = mod.assess()
        self.assertTrue(row["canonical_reasons_only"])
        self.assertTrue(row["all_fail_closed"])
        self.assertTrue(row["unique_blocker_ids"])
        self.assertEqual(row["status"], "HUMAN_REQUIRED_BLOCKERS_REGISTERED")

    def test_security_auth_identity_is_high_risk(self):
        security = next(x for x in mod.BLOCKERS if x["blocker_id"] == "SECURITY_AUTHENTICATED_HTTP_E2E_IDENTITY")
        self.assertEqual(security["reason"], "HIGH_RISK")
        self.assertFalse(security["automatic_action_allowed"])
        self.assertIn("selective_retirement_of_only_migrated_legacy_authenticated_execute_after_http_gate", security["unblocks"])

    def test_recovery_paid_fallback_is_money_limit(self):
        recovery = next(x for x in mod.BLOCKERS if x["blocker_id"] == "RECOVERY_PROVIDER_ISOLATED_RESTORE_TARGET")
        self.assertEqual(recovery["reason"], "MONEY_LIMIT")
        self.assertFalse(recovery["automatic_action_allowed"])


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "resilience"))
sys.path.insert(0, str(ROOT / "identity"))

from plan import RecoveryPlan
from model import CredentialRef, Connector


class ResilienceIdentityTests(unittest.TestCase):
    def test_recovery_plan_requires_all_verified(self):
        evidence = {"backup": "backup:e", "restore": "restore:e", "rollback": "rollback:e", "rebuild": "rebuild:e"}
        not_ready = RecoveryPlan(True, True, True, False, True, True, evidence)
        self.assertFalse(not_ready.promotion_ready())
        boolean_only = RecoveryPlan(True, True, True, True, True, True)
        self.assertFalse(boolean_only.promotion_ready())
        ready = RecoveryPlan(True, True, True, True, True, True, evidence)
        self.assertTrue(ready.promotion_ready())

    def test_credential_ref_rejects_embedded_secret_value(self):
        ref = CredentialRef("c1", "a1", "vault", "token=abc")
        with self.assertRaises(ValueError):
            ref.validate()

    def test_credential_ref_accepts_vault_reference(self):
        ref = CredentialRef("c1", "a1", "github-secrets", "CEREBRO/FENIX/API_TOKEN")
        ref.validate()

    def test_connector_type_is_limited(self):
        Connector("x", "MCP", "provider", "0.1.0").validate()
        with self.assertRaises(ValueError):
            Connector("x", "MAGIC", "provider", "0.1.0").validate()


if __name__ == "__main__":
    unittest.main()

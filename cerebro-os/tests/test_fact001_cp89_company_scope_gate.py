import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "factory" / "fact001_cp89_company_scope_gate.py"
spec = importlib.util.spec_from_file_location("cp89_gate", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CP89CompanyScopeGateTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / "config" / "improvement_companies.lab.json").read_text())
        self.instance = json.loads(
            (ROOT / "registry" / "instances" / "SUP-001_FACT001-P5_CP88.lab.json").read_text()
        )

    def test_live_cp88_fixture_fails_closed_on_company_id_mismatch(self):
        result = mod.assess_cp89_provisioning(registry_rows=self.registry, instance=self.instance)
        self.assertEqual(result["registry_company_id"], "fenix")
        self.assertEqual(result["runtime_company_id"], "fenix-capital")
        self.assertEqual(result["status"], "HOLD_COMPANY_ID_MISMATCH")
        self.assertFalse(result["aliases_automatically_assumed"])
        self.assertFalse(result["factory_provisioning_allowed"])
        self.assertFalse(result["iam_grant_allowed"])
        self.assertFalse(result["ums_enrollment_allowed"])
        self.assertEqual(result["next_gate"], "VERIFIED_SIGNED_COMPANY_ID_CONTRACT")

    def test_exact_company_match_still_does_not_convert_admin_seed_to_factory_provisioning(self):
        instance = dict(self.instance)
        instance["company_id"] = "fenix"
        result = mod.assess_cp89_provisioning(registry_rows=self.registry, instance=instance)
        self.assertEqual(result["status"], "HOLD_NOT_FACTORY_PROVISIONED")
        self.assertFalse(result["factory_provisioning_allowed"])
        self.assertEqual(result["next_gate"], "AUTHORIZED_FACTORY_ISSUER")

    def test_no_alias_or_invalid_company_id_is_accepted(self):
        with self.assertRaises(ValueError):
            mod.assess_company_scope(registry_company_id="fenix", runtime_company_id="FENIX_CAPITAL")
        mismatch = mod.assess_company_scope(registry_company_id="fenix", runtime_company_id="fenix-capital")
        self.assertFalse(mismatch["attribution_to_registry_allowed"])


if __name__ == "__main__":
    unittest.main()

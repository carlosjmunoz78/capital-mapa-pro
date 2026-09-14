import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAX_API = ROOT / "engines" / "TAX-001" / "api"
sys.path.insert(0, str(TAX_API))

from tax_engine import evaluate


class Tax001CapabilityTests(unittest.TestCase):
    def base_payload(self):
        return {
            "request_id": "req-tax-001",
            "company_id": "fenix-capital",
            "operation": "CALCULATE",
            "facts": {"taxpayer_type": "individual", "amount": 1000},
            "effective_date": "2026-09-15",
            "jurisdiction": "ES-AN",
            "evidence_refs": ["BOE:official-source-placeholder-id"],
        }

    def test_manifest_is_lab_and_prod_disabled(self):
        manifest = json.loads((ROOT / "engines" / "TAX-001" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine_id"], "TAX-001")
        self.assertEqual(manifest["environment"], "LAB")
        self.assertFalse(manifest["prod_enabled"])
        self.assertEqual(manifest["autonomy_level"], "DECISION_SUPPORT_ONLY")
        self.assertEqual(manifest["cost_budget"]["target_additional_eur"], 0)

    def test_regulated_external_action_fails_closed(self):
        payload = self.base_payload()
        payload["operation"] = "FILE"
        result = evaluate(payload)
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_required"], "LEGAL_REQUIRED")

    def test_missing_evidence_fails_closed(self):
        payload = self.base_payload()
        payload["evidence_refs"] = []
        result = evaluate(payload)
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_required"], "LOW_CONFIDENCE")

    def test_missing_facts_fails_closed(self):
        payload = self.base_payload()
        payload["facts"] = {}
        result = evaluate(payload)
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_required"], "LOW_CONFIDENCE")

    def test_valid_envelope_reaches_rule_execution_boundary(self):
        result = evaluate(self.base_payload())
        self.assertEqual(result["status"], "READY_FOR_RULE_EXECUTION")
        self.assertIsNone(result["human_required"])
        self.assertEqual(result["engine_id"], "TAX-001")
        self.assertEqual(result["cost_eur"], 0.0)

    def test_unknown_operation_is_denied(self):
        payload = self.base_payload()
        payload["operation"] = "DO_SOMETHING_UNDEFINED"
        result = evaluate(payload)
        self.assertEqual(result["status"], "DENY")
        self.assertEqual(result["human_required"], "POLICY_CONFLICT")


if __name__ == "__main__":
    unittest.main()

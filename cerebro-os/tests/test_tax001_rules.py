import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAX_ROOT = ROOT / "engines" / "TAX-001"
sys.path.insert(0, str(TAX_ROOT / "api"))
sys.path.insert(0, str(TAX_ROOT / "observability"))

from rule_executor import execute_rule, validate_corpus_lock
from audit import build_audit_event


HASHES = {
    "AW": "a" * 64,
    "AV": "b" * 64,
    "BH": "c" * 64,
}


def bound_lock():
    return {
        "status": "BOUND",
        "artifacts": {
            "AW": {"sha256": HASHES["AW"]},
            "AV": {"sha256": HASHES["AV"]},
            "BH": {"sha256": HASHES["BH"]},
        },
    }


def base_payload():
    return {
        "request_id": "req-rule-1",
        "company_id": "fenix-capital",
        "operation": "CALCULATE",
        "facts": {"base": "1000"},
        "effective_date": "2026-09-15",
        "jurisdiction": "ES-AN",
        "evidence_refs": ["official:test-source"],
    }


def base_rule():
    return {
        "rule_id": "TEST-RULE-001",
        "rule_version": "1.0.0",
        "jurisdiction": "ES-AN",
        "operation": "CALCULATE",
        "effective_from": "2026-01-01",
        "effective_to": "2026-12-31",
        "required_facts": ["base"],
        "evidence_refs": ["official:test-source"],
        "expression": {"type": "MULTIPLY_FACT_BY_RATE", "fact": "base", "rate": "0.10"},
    }


class Tax001RuleExecutorTests(unittest.TestCase):
    def test_unbound_corpus_fails_closed(self):
        result = execute_rule(base_payload(), base_rule(), {"status": "UNBOUND", "artifacts": {}}, HASHES)
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_required"], "LOW_CONFIDENCE")

    def test_hash_mismatch_fails_closed(self):
        wrong = dict(HASHES)
        wrong["BH"] = "d" * 64
        ok, reason = validate_corpus_lock(bound_lock(), wrong)
        self.assertFalse(ok)
        self.assertIn("BH", reason)

    def test_bound_current_rule_executes_deterministically(self):
        result = execute_rule(base_payload(), base_rule(), bound_lock(), HASHES)
        self.assertEqual(result["status"], "RULE_EXECUTED")
        self.assertEqual(result["value"], "100.00")
        self.assertTrue(result["corpus_lock_verified"])
        self.assertEqual(result["cost_eur"], 0.0)

    def test_out_of_range_effective_date_fails_closed(self):
        payload = base_payload()
        payload["effective_date"] = "2027-01-01"
        result = execute_rule(payload, base_rule(), bound_lock(), HASHES)
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_required"], "LOW_CONFIDENCE")

    def test_missing_required_fact_fails_closed(self):
        payload = base_payload()
        payload["facts"] = {}
        result = execute_rule(payload, base_rule(), bound_lock(), HASHES)
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_required"], "LOW_CONFIDENCE")

    def test_case_must_carry_rule_evidence(self):
        payload = base_payload()
        payload["evidence_refs"] = ["official:other-source"]
        result = execute_rule(payload, base_rule(), bound_lock(), HASHES)
        self.assertEqual(result["status"], "HUMAN_REQUIRED")
        self.assertEqual(result["human_required"], "LOW_CONFIDENCE")

    def test_audit_event_keeps_multicompany_trace_and_declares_no_persistence(self):
        payload = base_payload()
        result = execute_rule(payload, base_rule(), bound_lock(), HASHES)
        event = build_audit_event(payload, result, duration_ms=7)
        self.assertEqual(event["company_id"], "fenix-capital")
        self.assertEqual(event["engine_id"], "TAX-001")
        self.assertEqual(event["environment"], "LAB")
        self.assertEqual(event["rule_id"], "TEST-RULE-001")
        self.assertEqual(event["persistence_status"], "NOT_PERSISTED_BY_TAX001")
        self.assertEqual(event["persistence_owner"], "AUD-001")


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from dispatcher import DispatchCandidate, classify_candidate, summarize_query


class DispatcherRuntimeTests(unittest.TestCase):
    def candidate(self, **changes):
        data = dict(company_id="fenix-capital", engine_id="SOC-DISPATCH", environment="LAB", version="1.0.0", notion_record_id="N1", run_id="R1", platform="Instagram", technical_format="REEL", publication_state="Pendiente de publicar", integration_blocked=False, has_programming_relation=True, has_production_order=True, t48_approved=True, t48_approval_date_present=True, t48_locked_version_present=True, t48_hash_present=True, real_publication_authorization="Autorizada")
        data.update(changes)
        return DispatchCandidate(**data)

    def test_eligible_candidate_is_classified_but_never_executes(self):
        result = classify_candidate(self.candidate())
        self.assertEqual(result["status"], "ROUTE_PREPARED_ENGINE_OFF")
        self.assertEqual(result["platform_state"], "NOT_CALLED")
        self.assertFalse(result["external_action_allowed"])

    def test_missing_t48_gate_blocks(self):
        result = classify_candidate(self.candidate(t48_hash_present=False))
        self.assertEqual(result["status"], "BLOCKED_NOT_ELIGIBLE")
        self.assertFalse(result["external_action_allowed"])

    def test_query_receipt_preserves_no_execution_contract(self):
        result = summarize_query(3, company_id="fenix-capital", engine_id="SOC-DISPATCH", environment="LAB", version="1.0.0")
        self.assertEqual(result["status"], "CANDIDATES_CLASSIFIED_NO_EXECUTION")
        self.assertFalse(result["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()

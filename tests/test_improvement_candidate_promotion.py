import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.plan_improvement_candidate_promotion import plan


class PromotionGateTests(unittest.TestCase):
    def _run(self, candidate: dict, tribunal: dict, canary: dict) -> dict:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidates = root / "candidates"
            evidence = root / "evidence"
            candidates.mkdir()
            evidence.mkdir()
            (candidates / "aion.json").write_text(json.dumps(candidate), encoding="utf-8")
            (evidence / "aion.tribunal.json").write_text(json.dumps(tribunal), encoding="utf-8")
            (evidence / "aion.canary.json").write_text(json.dumps(canary), encoding="utf-8")
            old = os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_CANDIDATES_ROOT"] = str(candidates)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"] = str(evidence)
            try:
                plan()
            finally:
                os.environ.clear()
                os.environ.update(old)
            return json.loads((evidence / "aion.promote_or_rollback.json").read_text())

    def test_local_canary_never_promotes(self):
        payload = self._run(
            {
                "company_id": "aion",
                "candidates": [{
                    "proposal_id": "p1",
                    "target": "https://example.com/",
                    "change_spec": {"operation": "SET_CANONICAL", "value": "https://example.com/"},
                }],
            },
            {
                "company_id": "aion", "stage": "TRIBUNAL", "status": "GREEN",
                "production_approval": False, "external_mutation_allowed": False,
            },
            {
                "company_id": "aion", "stage": "CANARY", "status": "GREEN",
                "canary_scope": "LOCAL_SIMULATION_ONLY", "live_traffic_exposed": False,
                "live_effect_verified": False, "production_ready": False,
                "external_mutation_allowed": False,
            },
        )
        self.assertEqual(payload["status"], "WAITING")
        self.assertEqual(payload["decision"], "HOLD_FOR_LIVE_CANARY")
        self.assertFalse(payload["promotion_allowed"])
        self.assertFalse(payload["progressive_delivery_allowed"])
        self.assertTrue(payload["rollback_supported"])
        self.assertEqual(payload["rollback_plan"][0]["operation"], "RESTORE_PREVIOUS_CANONICAL")

    def test_unsupported_rollback_stays_closed(self):
        payload = self._run(
            {
                "company_id": "aion",
                "candidates": [{
                    "proposal_id": "p1",
                    "target": "content",
                    "change_spec": {"operation": "RESEARCH_AND_PROPOSE"},
                }],
            },
            {
                "company_id": "aion", "stage": "TRIBUNAL", "status": "GREEN",
                "production_approval": False, "external_mutation_allowed": False,
            },
            {
                "company_id": "aion", "stage": "CANARY", "status": "GREEN",
                "canary_scope": "LOCAL_SIMULATION_ONLY", "live_traffic_exposed": False,
                "live_effect_verified": False, "production_ready": False,
                "external_mutation_allowed": False,
            },
        )
        self.assertEqual(payload["decision"], "HOLD_FOR_ROLLBACK")
        self.assertFalse(payload["rollback_supported"])

    def test_cross_company_canary_is_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            candidates = root / "candidates"
            evidence = root / "evidence"
            candidates.mkdir()
            evidence.mkdir()
            (candidates / "aion.json").write_text(json.dumps({
                "company_id": "aion", "candidates": []
            }), encoding="utf-8")
            (evidence / "aion.canary.json").write_text(json.dumps({
                "company_id": "fenix", "stage": "CANARY"
            }), encoding="utf-8")
            old = os.environ.copy()
            os.environ["CEREBRO_IMPROVEMENT_CANDIDATES_ROOT"] = str(candidates)
            os.environ["CEREBRO_IMPROVEMENT_EVIDENCE_ROOT"] = str(evidence)
            try:
                with self.assertRaisesRegex(ValueError, "cross-company CANARY"):
                    plan()
            finally:
                os.environ.clear()
                os.environ.update(old)


if __name__ == "__main__":
    unittest.main()

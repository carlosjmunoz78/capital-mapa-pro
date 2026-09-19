import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from learning.progressive_delivery import DeliveryEvidence, decide_progressive_delivery


class ProgressiveDeliveryGuardTests(unittest.TestCase):
    def test_lab_and_preprod_never_advance_live_delivery(self):
        for env in ("LAB", "PREPROD"):
            d = decide_progressive_delivery(DeliveryEvidence(
                baseline_value=10, candidate_value=11, direction="MAXIMIZE",
                sample_size=100, minimum_sample_size=20, live_effect_verified=True,
                rollback_ready=True, policy_approved=True, environment=env,
                current_percent=1,
            ))
            self.assertEqual(d.decision, "HOLD")
            self.assertEqual(d.reason, "PROD_EVIDENCE_REQUIRED")

    def test_missing_live_effect_or_rollback_or_policy_fail_closed(self):
        base = dict(
            baseline_value=10, candidate_value=11, direction="MAXIMIZE",
            sample_size=100, minimum_sample_size=20, environment="PROD",
            current_percent=1,
        )
        cases = [
            (False, True, True, "LIVE_EFFECT_NOT_VERIFIED"),
            (True, False, True, "ROLLBACK_NOT_READY"),
            (True, True, False, "POLICY_NOT_APPROVED"),
        ]
        for live, rollback, policy, reason in cases:
            d = decide_progressive_delivery(DeliveryEvidence(
                **base, live_effect_verified=live,
                rollback_ready=rollback, policy_approved=policy,
            ))
            self.assertEqual(d.decision, "HOLD")
            self.assertEqual(d.reason, reason)

    def test_insufficient_sample_requests_more_evidence(self):
        d = decide_progressive_delivery(DeliveryEvidence(
            baseline_value=10, candidate_value=11, direction="MAXIMIZE",
            sample_size=5, minimum_sample_size=20, live_effect_verified=True,
            rollback_ready=True, policy_approved=True, environment="PROD",
            current_percent=1,
        ))
        self.assertEqual(d.decision, "HOLD")
        self.assertEqual(d.reason, "MORE_EVIDENCE")

    def test_regression_requires_rollback(self):
        d = decide_progressive_delivery(DeliveryEvidence(
            baseline_value=10, candidate_value=9, direction="MAXIMIZE",
            sample_size=100, minimum_sample_size=20, live_effect_verified=True,
            rollback_ready=True, policy_approved=True, environment="PROD",
            current_percent=25,
        ))
        self.assertEqual(d.decision, "ROLLBACK")
        self.assertTrue(d.rollback_required)

    def test_green_evidence_advances_gradually(self):
        expected = {1: 5, 5: 25, 25: 50, 50: 100}
        for current, nxt in expected.items():
            d = decide_progressive_delivery(DeliveryEvidence(
                baseline_value=10, candidate_value=11, direction="MAXIMIZE",
                sample_size=100, minimum_sample_size=20, live_effect_verified=True,
                rollback_ready=True, policy_approved=True, environment="PROD",
                current_percent=current,
            ))
            self.assertEqual(d.decision, "ADVANCE")
            self.assertEqual(d.next_percent, nxt)

    def test_full_delivery_stays_monitored(self):
        d = decide_progressive_delivery(DeliveryEvidence(
            baseline_value=10, candidate_value=11, direction="MAXIMIZE",
            sample_size=100, minimum_sample_size=20, live_effect_verified=True,
            rollback_ready=True, policy_approved=True, environment="PROD",
            current_percent=100,
        ))
        self.assertEqual(d.decision, "MONITOR")
        self.assertEqual(d.reason, "FULL_DELIVERY_MONITOR")


if __name__ == "__main__":
    unittest.main()

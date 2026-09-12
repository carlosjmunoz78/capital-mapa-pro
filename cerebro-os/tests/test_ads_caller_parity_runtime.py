import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from ads_caller_parity import ADS_CORE_SCENARIO_ID, AdsCutoverEvidence, assess_ads_cutover


class AdsCallerParityTests(unittest.TestCase):
    def test_live_scenario_id_is_canonical(self):
        self.assertEqual(ADS_CORE_SCENARIO_ID, 9535463)

    def test_cutover_blocks_without_runtime_and_money_safety(self):
        out = assess_ads_cutover(AdsCutoverEvidence(
            scenario_id=9535463,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            target_runtime_live=False,
            old_preserved=True,
            money_gate_safe=False,
        ))
        self.assertFalse(out["cutover_ready"])
        self.assertIn("TARGET_RUNTIME_NOT_LIVE", out["blockers"])
        self.assertIn("MONEY_GATE_NOT_SAFE", out["blockers"])
        self.assertFalse(out["external_action_allowed"])

    def test_all_gates_green_still_requires_money_limit_human_gate(self):
        out = assess_ads_cutover(AdsCutoverEvidence(
            scenario_id=9535463,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            target_runtime_live=True,
            old_preserved=True,
            money_gate_safe=True,
        ))
        self.assertTrue(out["cutover_ready"])
        self.assertTrue(out["deactivate_old_allowed"])
        self.assertFalse(out["delete_old_allowed"])
        self.assertFalse(out["external_action_allowed"])
        self.assertEqual(out["human_reason"], "MONEY_LIMIT")

    def test_live_fixture_preserves_no_external_action_contract(self):
        data = json.loads((ROOT / "runtime" / "fixtures" / "ads_core_live_contract.json").read_text(encoding="utf-8"))
        self.assertEqual(data["scenario_id"], 9535463)
        self.assertEqual(data["old_contract"]["preflight_status"], "ADS_PREFLIGHT_READY_ENGINE_DISABLED")
        self.assertEqual(data["old_contract"]["router_receipt_status"], "ADS_ROUTED_NO_EXTERNAL_ACTION")
        self.assertFalse(data["old_contract"]["external_action"])
        self.assertFalse(data["new_runtime_invariants"]["external_action_allowed"])


if __name__ == "__main__":
    unittest.main()

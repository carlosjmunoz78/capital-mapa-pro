import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ADVISORY_DIR = ROOT / "advisory"


class AdvisoryBlockEClosureTests(unittest.TestCase):
    def test_canonical_status_preserves_preprod_green_and_global_prod_off(self):
        status = json.loads(
            (ADVISORY_DIR / "capability_status_20260915.json").read_text(encoding="utf-8")
        )
        runtime = status["capability_runtime"]
        self.assertTrue(runtime["capability_green_preprod"])
        self.assertTrue(runtime["advisory_autonomy_preprod_green"])
        self.assertFalse(runtime["capability_green_global"])
        self.assertFalse(status["autonomy_green"])
        self.assertFalse(status["prod_enabled"])
        self.assertFalse(status["app_crm_prod_touched"])
        self.assertEqual(status["additional_cost_target_eur"], 0)

    def test_continuity_state_has_green_a_to_d_and_safe_flags(self):
        state = json.loads(
            (ADVISORY_DIR / "ADVISORY_CONTINUITY_STATE_20260915.json").read_text(
                encoding="utf-8"
            )
        )
        for block in ("A", "B", "C", "D"):
            self.assertEqual(state["blocks"][block]["status"], "GREEN")
        self.assertTrue(state["flags"]["preprod_enabled"])
        self.assertTrue(state["flags"]["capability_green_preprod"])
        self.assertFalse(state["flags"]["autonomy_green"])
        self.assertFalse(state["flags"]["prod_enabled"])
        self.assertFalse(state["flags"]["app_crm_prod_touched"])
        self.assertEqual(len(state["human_required_codes"]), 8)

    def test_required_closure_docs_exist(self):
        for name in (
            "ADVISORY_DEPENDENCY_MAP.md",
            "ADVISORY_RUNBOOK.md",
            "ADVISORY_CHANGELOG_20260915.md",
            "ADVISORY_CONTINUITY_STATE_20260915.json",
        ):
            with self.subTest(name=name):
                self.assertTrue((ADVISORY_DIR / name).is_file())


if __name__ == "__main__":
    unittest.main()

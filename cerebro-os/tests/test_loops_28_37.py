import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


loops = load("platform_loops_28_37", "processes/platform_loops_28_37.py")
controller_mod = load("platform_loop_controller_28_37", "processes/platform_loop_controller.py")


class Loops28To37Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "registry/canonical_177.json").read_text(encoding="utf-8"))
        cls.canonical = set(data["engine_ids"])

    def test_exactly_ten_loops_all_canonical_unique(self):
        self.assertEqual(10, len(loops.LOOPS_28_37))
        loops.validate_against_canonical(self.canonical)
        ids = loops.all_engine_ids()
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_loop_can_close_green_with_evidence(self):
        ctl = controller_mod.PlatformLoopController("fenix", loops.LOOPS_28_37, loops.LAB_ONLY_ENGINES)
        for loop_id, sequence in loops.LOOPS_28_37.items():
            self.assertEqual(loop_id, ctl.next_loop())
            for engine_id in sequence:
                self.assertEqual(engine_id, ctl.next_engine(loop_id))
                ctl.update(controller_mod.EngineResult(
                    "fenix", loop_id, engine_id, "LAB", "GREEN", f"evidence:{loop_id}:{engine_id}"
                ))
            self.assertEqual("GREEN", ctl.loop_status(loop_id))
        self.assertEqual("GREEN", ctl.system_status())
        self.assertIsNone(ctl.next_loop())

    def test_out_of_order_green_is_blocked(self):
        loop_id = "LOOP-31-SECURITY-RESILIENCE"
        seq = loops.LOOPS_28_37[loop_id]
        ctl = controller_mod.PlatformLoopController("fenix", {loop_id: seq}, loops.LAB_ONLY_ENGINES)
        with self.assertRaises(ValueError):
            ctl.update(controller_mod.EngineResult("fenix", loop_id, "SEC-002", "LAB", "GREEN", "evidence:x"))

    def test_cross_company_is_denied(self):
        loop_id = "LOOP-37-CONSOLE-UI"
        seq = loops.LOOPS_28_37[loop_id]
        ctl = controller_mod.PlatformLoopController("fenix", {loop_id: seq}, loops.LAB_ONLY_ENGINES)
        with self.assertRaises(ValueError):
            ctl.update(controller_mod.EngineResult("other", loop_id, seq[0], "LAB", "GREEN", "evidence:x"))

    def test_human_required_reasons_are_canonical(self):
        loop_id = "LOOP-28-CORE-GOVERNANCE"
        seq = loops.LOOPS_28_37[loop_id]
        ctl = controller_mod.PlatformLoopController("fenix", {loop_id: seq}, loops.LAB_ONLY_ENGINES)
        ctl.update(controller_mod.EngineResult("fenix", loop_id, seq[0], "LAB", "HUMAN_REQUIRED", human_reason="POLICY_CONFLICT"))
        self.assertEqual("HUMAN_REQUIRED", ctl.loop_status(loop_id))
        with self.assertRaises(ValueError):
            ctl.update(controller_mod.EngineResult("fenix", loop_id, seq[0], "LAB", "HUMAN_REQUIRED", human_reason="UNKNOWN"))

    def test_lab_engines_cannot_enter_prod(self):
        loop_id = "LOOP-35-LABS"
        seq = loops.LOOPS_28_37[loop_id]
        ctl = controller_mod.PlatformLoopController("fenix", {loop_id: seq}, loops.LAB_ONLY_ENGINES)
        with self.assertRaises(ValueError):
            ctl.update(controller_mod.EngineResult("fenix", loop_id, "LAB-TRD", "PROD", "GREEN", "evidence:bad"))

    def test_green_requires_evidence(self):
        loop_id = "LOOP-33-APP-DATA-PLATFORM"
        seq = loops.LOOPS_28_37[loop_id]
        ctl = controller_mod.PlatformLoopController("fenix", {loop_id: seq}, loops.LAB_ONLY_ENGINES)
        with self.assertRaises(ValueError):
            ctl.update(controller_mod.EngineResult("fenix", loop_id, seq[0], "LAB", "GREEN"))


if __name__ == "__main__":
    unittest.main()

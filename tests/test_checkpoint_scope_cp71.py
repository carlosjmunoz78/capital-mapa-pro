"""CP71: fail-closed checkpoint replay without modifying the external runner."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))
from learning.continuous_improvement_runtime import RuntimeSnapshot, StageResult
from learning.improvement_checkpoint_store import ImprovementCheckpointStore


def snap(*stages, company="fenix", profile="FENIX_SENSITIVE", env="LAB", version="1.0.0", status="IN_PROGRESS"):
    return RuntimeSnapshot(company, profile, env, version, tuple(stages), status)


class CheckpointScopeCP71(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "learning.sqlite"
        self.store = ImprovementCheckpointStore(self.path)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_scope_profile_cannot_be_replaced(self):
        original = snap(StageResult("OBSERVE", "GREEN", "e://1"))
        self.store.save(original)
        with self.assertRaises(PermissionError):
            self.store.save(snap(StageResult("OBSERVE", "GREEN", "e://1"), profile="AUTONOMOUS_VENTURE"))
        self.assertEqual(self.store.load(company_id="fenix",environment="LAB",version="1.0.0"), original)

    def test_green_evidence_is_immutable(self):
        original = snap(StageResult("OBSERVE", "GREEN", "e://original"))
        self.store.save(original)
        with self.assertRaises(PermissionError):
            self.store.save(snap(StageResult("OBSERVE", "GREEN", "e://tampered")))
        self.assertEqual(self.store.load(company_id="fenix",environment="LAB",version="1.0.0"), original)

    def test_truncation_rejected(self):
        original = snap(StageResult("OBSERVE","GREEN","e://1"),StageResult("MEASURE","WAITING","e://w"),status="WAITING")
        self.store.save(original)
        with self.assertRaises(PermissionError):
            self.store.save(snap(StageResult("OBSERVE","GREEN","e://1")))

    def test_completed_terminal_checkpoint_cannot_be_reopened(self):
        stages = tuple(StageResult(k,"GREEN",f"e://{k}") for k in (
            "OBSERVE", "MEASURE", "DETECT", "PROPOSE", "LAB", "TEST", "EVALUATE", "TRIBUNAL", "OLD_VS_NEW", "CANARY", "PROMOTE_OR_ROLLBACK", "LEARN"))
        original = snap(*stages,status="GREEN")
        self.store.save(original)
        with self.assertRaises(PermissionError):
            self.store.save(snap(*stages,status="IN_PROGRESS"))
        self.assertEqual(self.store.load(company_id="fenix",environment="LAB",version="1.0.0"),original)

    def test_pending_resolution_and_next_stage_are_allowed(self):
        first = snap(StageResult("OBSERVE", "GREEN", "e://observe"),StageResult("MEASURE", "WAITING", "e://pending"),status="WAITING")
        self.store.save(first)
        second = snap(StageResult("OBSERVE", "GREEN", "e://observe"),StageResult("MEASURE", "GREEN", "e://measured"),StageResult("DETECT", "WAITING", "e://detect"),status="WAITING")
        self.store.save(second)
        self.assertEqual(self.store.load(company_id="fenix",environment="LAB",version="1.0.0"),second)

    def test_repeat_same_checkpoint_is_idempotent(self):
        first=snap(StageResult("OBSERVE","GREEN","e://1"))
        self.store.save(first)
        self.store.save(first)
        self.assertEqual(self.store.load(company_id="fenix",environment="LAB",version="1.0.0"),first)

    def test_bad_stage_order_rejected_even_initial_write(self):
        with self.assertRaises(ValueError):
            self.store.save(snap(StageResult("MEASURE","GREEN","e://2")))
        self.assertIsNone(self.store.load(company_id="fenix",environment="LAB",version="1.0.0"))

    def test_false_green_is_denied(self):
        with self.assertRaises(ValueError):
            self.store.save(snap(StageResult("OBSERVE", "GREEN", "e://1"),status="GREEN"))

    def test_cross_company_writes_remain_independent(self):
        self.store.save(snap(StageResult("OBSERVE","GREEN","e://fenix")))
        other=snap(StageResult("OBSERVE","GREEN","e://aion"),company="aion",profile="AUTONOMOUS_VENTURE")
        self.store.save(other)
        self.assertEqual(self.store.load(company_id="aion",environment="LAB",version="1.0.0"),other)

    def test_two_connections_cannot_overwrite_confirmed_stage(self):
        original=snap(StageResult("OBSERVE","GREEN","e://one"))
        self.store.save(original)
        second=ImprovementCheckpointStore(self.path)
        try:
            with self.assertRaises(PermissionError):
                second.save(snap(StageResult("OBSERVE","GREEN","e://two")))
        finally:
            second.close()
        self.assertEqual(self.store.load(company_id="fenix",environment="LAB",version="1.0.0"),original)


if __name__=="__main__":
    unittest.main()
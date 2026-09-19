import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from learning.continuous_improvement_runtime import RuntimeSnapshot, StageResult
from learning.improvement_checkpoint_store import ImprovementCheckpointStore


class CheckpointTests(unittest.TestCase):
    def test_roundtrip_waiting_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementCheckpointStore(Path(td) / "state.db")
            snap = RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (
                StageResult("OBSERVE", "GREEN", "e://observe"),
                StageResult("MEASURE", "WAITING", "e://waiting"),
            ), "WAITING")
            store.save(snap)
            loaded = store.load(company_id="aion", environment="LAB", version="1.0.0")
            self.assertEqual(loaded, snap)
            store.close()

    def test_company_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementCheckpointStore(Path(td) / "state.db")
            snap = RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (), "IN_PROGRESS")
            store.save(snap)
            self.assertIsNone(store.load(company_id="fenix", environment="LAB", version="1.0.0"))
            store.close()

    def test_environment_isolation(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementCheckpointStore(Path(td) / "state.db")
            store.save(RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (), "IN_PROGRESS"))
            self.assertIsNone(store.load(company_id="aion", environment="PREPROD", version="1.0.0"))
            store.close()

    def test_upsert_replaces_same_scope(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementCheckpointStore(Path(td) / "state.db")
            store.save(RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (), "IN_PROGRESS"))
            final = RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (StageResult("OBSERVE", "GREEN", "e://x"),), "IN_PROGRESS")
            store.save(final)
            self.assertEqual(store.load(company_id="aion", environment="LAB", version="1.0.0"), final)
            store.close()

    def test_delete_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            store = ImprovementCheckpointStore(Path(td) / "state.db")
            store.save(RuntimeSnapshot("aion", "AUTONOMOUS_VENTURE", "LAB", "1.0.0", (), "IN_PROGRESS"))
            store.delete(company_id="aion", environment="LAB", version="1.0.0")
            self.assertIsNone(store.load(company_id="aion", environment="LAB", version="1.0.0"))
            store.close()

if __name__ == "__main__":
    unittest.main()

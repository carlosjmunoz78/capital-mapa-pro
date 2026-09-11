import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


canonical = load("l1012_canonical", "registry/canonical_loader.py")
gaps = load("l1012_gap", "factory/gap_closer.py")
batch = load("l1012_batch", "factory/batch_gap.py")
readiness = load("l1012_readiness", "registry/readiness_matrix.py")
auditq = load("l1012_auditq", "registry/audit_queue.py")
system_gate = load("l1012_system", "registry/system_gate.py")


class LoopsTenToTwelveTests(unittest.TestCase):
    def test_loop10_batch_gap_queue_spans_all_canonical_engines(self):
        ids = canonical.canonical_engine_ids()
        complete_present = set(gaps.STANDARD_REQUIREMENTS)
        present = {"FACT-001": complete_present}
        queue = batch.build_batch_gap_queue(
            canonical_ids=ids,
            present_by_engine=present,
            standard_requirements=gaps.STANDARD_REQUIREMENTS,
        )
        self.assertEqual(176, len(queue))
        self.assertEqual(1, batch.completed_count(canonical_ids=ids, queue=queue))
        self.assertNotIn("FACT-001", {row["engine_id"] for row in queue})

    def test_loop11_audit_queue_prioritizes_blocked_before_unknown(self):
        matrix = (
            {"engine_id": "CORE-001", "state": "UNKNOWN_REQUIRES_AUDIT"},
            {"engine_id": "GOV-001", "state": "BLOCKED"},
            {"engine_id": "FACT-001", "state": "LAB_GREEN"},
            {"engine_id": "POL-001", "state": "DOCUMENTED_PARTIAL"},
        )
        queue = auditq.build_audit_queue(matrix)
        self.assertEqual("GOV-001", queue[0]["engine_id"])
        self.assertEqual("CORE-001", queue[1]["engine_id"])
        self.assertNotIn("FACT-001", {row["engine_id"] for row in queue})

    def test_loop12_system_gate_cannot_turn_green_with_unknown_engines(self):
        ids = canonical.canonical_engine_ids()
        matrix = readiness.build_readiness_matrix(canonical_ids=ids, live_records=[])
        state = system_gate.system_readiness(canonical_ids=ids, matrix=matrix)
        self.assertEqual("RED", state["state"])
        self.assertEqual(0, state["green_count"])
        all_green = tuple({"engine_id": engine_id, "state": "LAB_GREEN"} for engine_id in ids)
        green = system_gate.system_readiness(canonical_ids=ids, matrix=all_green)
        self.assertEqual("GREEN", green["state"])
        self.assertEqual(177, green["green_count"])


if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cerebro-os"))

from jobs.improvement_operations_registry import ImprovementCompanyConfig, ImprovementOperationsRegistry
from jobs.improvement_shared_worker import SharedImprovementWorker, WorkerPaths
from learning.continuous_improvement_runtime import StageResult
from console.improvement_status import export_console_status
from resilience.improvement_state_bundle import backup_improvement_state, rebuild_improvement_state


class ImprovementOperationsTests(unittest.TestCase):
    def test_registry_worker_console_backup_rebuild(self):
        now = datetime(2026,9,19,12,0,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            registry = ImprovementOperationsRegistry(root/"registry.db")
            registry.upsert(ImprovementCompanyConfig("aion","AION","AUTONOMOUS_VENTURE"))
            registry.upsert(ImprovementCompanyConfig("fenix","Fenix Capital","FENIX_DIGITAL"))
            worker = SharedImprovementWorker(registry, WorkerPaths(root/"state"))
            result, supervisor = worker.run(now, lambda company: (lambda s,a: StageResult(s,"GREEN",f"e://{company}/{s}")))
            self.assertEqual(result.green,2)
            self.assertEqual(supervisor["status"],"GREEN")

            status = export_console_status(root/"state", (
                {"company_id":"aion","environment":"LAB","version":"1.0.0"},
                {"company_id":"fenix","environment":"LAB","version":"1.0.0"},
            ))
            self.assertEqual(status["count"],2)
            self.assertTrue(all(x["audit_present"] for x in status["companies"]))

            manifest = backup_improvement_state(root/"backups", root/"state", company_id="aion", environment="LAB", version="1.0.0")
            rebuilt_root = root/"rebuilt"
            self.assertTrue(rebuild_improvement_state(root/"backups", manifest, rebuilt_root))
            self.assertTrue((rebuilt_root/"aion"/"LAB"/"1.0.0"/"audit.db").exists())
            registry.close()

    def test_disabled_company_is_skipped(self):
        now = datetime(2026,9,19,12,0,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            registry=ImprovementOperationsRegistry(root/"registry.db")
            registry.upsert(ImprovementCompanyConfig("off","Off Co","AUTONOMOUS_VENTURE",enabled=False))
            result,_=SharedImprovementWorker(registry,WorkerPaths(root/"state")).run(now,lambda c:(lambda s,a:StageResult(s,"GREEN","e://x")))
            self.assertEqual(len(result.outcomes),0)
            registry.close()

if __name__=="__main__":
    unittest.main()

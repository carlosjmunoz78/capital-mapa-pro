import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "observability_store.py"
spec = importlib.util.spec_from_file_location("observability_store", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ObservabilityStore177Tests(unittest.TestCase):
    def test_all_177_engines_have_lab_log_metric_incident_coverage(self):
        payload = json.loads((ROOT / "registry" / "canonical_177.json").read_text(encoding="utf-8"))
        engines = tuple(payload["engine_ids"])
        self.assertEqual(len(engines), 177)
        with tempfile.TemporaryDirectory() as td:
            store = module.SQLiteObservabilityStore(pathlib.Path(td) / "obs.sqlite3")
            try:
                for engine_id in engines:
                    for kind in ("log", "metric", "incident"):
                        store.append(module.ObservabilityEvent(
                            company_id="fenix_capital",
                            engine_id=engine_id,
                            environment="LAB",
                            version="0.1.0",
                            kind=kind,
                            name=f"coverage.{kind}",
                            payload={"synthetic": True, "engine_id": engine_id},
                            evidence_ref=f"CI:{engine_id}:{kind}",
                            cost_eur=0.0,
                        ))
                coverage = store.coverage("fenix_capital", "LAB", engines)
                self.assertEqual(coverage["required_engine_count"], 177)
                self.assertEqual(coverage["log_engine_count"], 177)
                self.assertEqual(coverage["metric_engine_count"], 177)
                self.assertEqual(coverage["incident_engine_count"], 177)
                self.assertTrue(coverage["all_required_engines_have_log"])
                self.assertTrue(coverage["all_required_engines_have_metric"])
                self.assertTrue(coverage["all_required_engines_have_incident"])
                self.assertFalse(coverage["additional_subscription_required"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()

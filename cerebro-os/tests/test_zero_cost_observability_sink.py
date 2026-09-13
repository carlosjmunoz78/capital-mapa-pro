import importlib.util
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "runtime" / "zero_cost_observability_sink.py"
spec = importlib.util.spec_from_file_location("zero_cost_observability_sink", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ZeroCostObservabilitySinkTests(unittest.TestCase):
    def event(self, kind, engine="FACT-001"):
        return {
            "company_id": "fenix-capital",
            "engine_id": engine,
            "environment": "LAB",
            "version": "v0",
            "kind": kind,
            "message": f"{kind}-ok",
        }

    def test_persists_replays_and_scopes_log_metric_incident(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "observability" / "events.jsonl"
            sink = module.JsonlObservabilitySink(path)
            for kind in ("log", "metric", "incident"):
                sink.append(self.event(kind))
            sink.append(self.event("log", engine="SEO-001"))
            replay = sink.replay()
            scoped = sink.scoped(company_id="fenix-capital", engine_id="FACT-001", environment="LAB", version="v0")
            self.assertEqual(len(replay), 4)
            self.assertEqual(len(scoped), 3)
            self.assertEqual(module.coverage(scoped), {"incident": True, "log": True, "metric": True})
            self.assertTrue(path.exists())

    def test_missing_multiempresa_scope_fails_closed(self):
        event = self.event("log")
        del event["company_id"]
        with tempfile.TemporaryDirectory() as tmp:
            sink = module.JsonlObservabilitySink(pathlib.Path(tmp) / "events.jsonl")
            with self.assertRaises(ValueError):
                sink.append(event)

    def test_secret_like_fields_are_rejected(self):
        event = self.event("incident")
        event["details"] = {"access_token": "must-not-persist"}
        with tempfile.TemporaryDirectory() as tmp:
            sink = module.JsonlObservabilitySink(pathlib.Path(tmp) / "events.jsonl")
            with self.assertRaises(ValueError):
                sink.append(event)

    def test_corrupt_jsonl_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "events.jsonl"
            path.write_text("{broken}\n", encoding="utf-8")
            sink = module.JsonlObservabilitySink(path)
            with self.assertRaises(ValueError):
                sink.replay()


if __name__ == "__main__":
    unittest.main()

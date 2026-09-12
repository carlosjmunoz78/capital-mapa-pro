import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from core_inactive_migration_policy import CoreInactiveScenario, classify_core_inactive


class CoreInactiveMigrationPolicyTests(unittest.TestCase):
    def item(self, **overrides):
        data = dict(scenario_id=1, name="FENIX · CORE · Router Maestro · V1", apps=("datastore",), incomplete_executions=0)
        data.update(overrides)
        return CoreInactiveScenario(**data)

    def test_deterministic_router_migrates_to_runtime(self):
        out = classify_core_inactive(self.item())
        self.assertEqual(out["disposition"], "MIGRATE_DETERMINISTIC_LOGIC_TO_RUNTIME")
        self.assertTrue(out["old_preserved"])
        self.assertFalse(out["delete_allowed"])

    def test_social_read_edge_is_kept_wrapped(self):
        out = classify_core_inactive(self.item(name="FENIX · CORE · YouTube · Captura analítica 24h", apps=("youtube", "datastore")))
        self.assertEqual(out["disposition"], "KEEP_SAAS_READ_EDGE_WRAP")
        self.assertFalse(out["external_action_allowed"])

    def test_tiktok_is_parked(self):
        out = classify_core_inactive(self.item(name="FENIX · CORE · TikTok · Router y preflight universal · V1"))
        self.assertEqual(out["disposition"], "PARKED_ACCOUNT_NOT_AVAILABLE")

    def test_historical_no_usar_is_quarantined(self):
        out = classify_core_inactive(self.item(name="FENIX · AUDITORÍA · WordPress · Corrección REST fallida · NO USAR", apps=("wordpress",)))
        self.assertEqual(out["disposition"], "QUARANTINE_HISTORICAL")

    def test_migrate_to_native_temp_is_explicit(self):
        out = classify_core_inactive(self.item(name="TEMPORAL · MIGRAR A NATIVO · FENIX · FÁBRICA · Adaptador generación de imágenes · V1", apps=("openai-gpt-3", "google-drive")))
        self.assertEqual(out["disposition"], "MIGRATE_TO_NATIVE_RUNTIME_KEEP_INACTIVE")

    def test_factory_adapter_moves_to_factory_runtime(self):
        out = classify_core_inactive(self.item(name="FENIX · FÁBRICA · Adaptador voz TTS · V1"))
        self.assertEqual(out["disposition"], "MIGRATE_TO_ENGINE_FACTORY_RUNTIME")

    def test_incomplete_execution_is_high_risk(self):
        out = classify_core_inactive(self.item(incomplete_executions=1))
        self.assertEqual(out["disposition"], "BLOCKED_REVIEW")
        self.assertTrue(out["human_required"])
        self.assertEqual(out["human_reason"], "HIGH_RISK")

    def test_preprod_wordpress_stays_fail_closed(self):
        out = classify_core_inactive(self.item(name="FÉNIX · PRE-PROD · CEREBRO SEO · WordPress lectura segura · V1", apps=("wordpress",)))
        self.assertEqual(out["disposition"], "KEEP_QUARANTINED_FAIL_CLOSED")


if __name__ == "__main__":
    unittest.main()

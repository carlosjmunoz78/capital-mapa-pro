import os
import sys
import unittest

HERE = os.path.dirname(__file__)
RUNTIME = os.path.abspath(os.path.join(HERE, "..", "runtime"))
if RUNTIME not in sys.path:
    sys.path.insert(0, RUNTIME)

from make_scenario_classification import MakeScenarioMeta, classify_scenario


class MakeScenarioClassificationTests(unittest.TestCase):
    def meta(self, **overrides):
        data = dict(
            scenario_id=1,
            name="FENIX · TEST · Read only",
            status="inactive",
            is_active=False,
            apps=("datastore",),
            incomplete_executions=0,
        )
        data.update(overrides)
        return MakeScenarioMeta(**data)

    def test_active_edge_is_preserved(self):
        out = classify_scenario(self.meta(status="active", is_active=True, apps=("google-search-console",)))
        self.assertEqual(out["classification"], "PRESERVE_ACTIVE_EDGE")
        self.assertFalse(out["auto_activate_allowed"])
        self.assertFalse(out["delete_allowed"])

    def test_error_is_archival_not_repaired_by_activation(self):
        out = classify_scenario(self.meta(status="error", name="historical invalid"))
        self.assertEqual(out["classification"], "ARCHIVE_TRACEABILITY_DO_NOT_RUN")
        self.assertFalse(out["auto_activate_allowed"])

    def test_deprecated_is_quarantined(self):
        out = classify_scenario(self.meta(name="DEPRECATED · NO USAR · old"))
        self.assertEqual(out["classification"], "QUARANTINE_DEPRECATED")

    def test_fixture_is_quarantined(self):
        out = classify_scenario(self.meta(name="FIXTURE · isolated"))
        self.assertEqual(out["classification"], "QUARANTINE_FIXTURE")

    def test_temp_is_quarantined(self):
        out = classify_scenario(self.meta(name="TEMPORAL · one shot"))
        self.assertEqual(out["classification"], "QUARANTINE_TEMPORARY")

    def test_inactive_mutator_is_never_auto_activated(self):
        out = classify_scenario(self.meta(name="publisher", apps=("facebook-pages", "notion")))
        self.assertEqual(out["classification"], "KEEP_INACTIVE_WRAP_AND_TEST")
        self.assertTrue(out["mutating_surface"])
        self.assertFalse(out["external_action_allowed"])

    def test_incomplete_executions_raise_high_risk(self):
        out = classify_scenario(self.meta(incomplete_executions=2))
        self.assertEqual(out["classification"], "REVIEW_REQUIRED")
        self.assertTrue(out["human_required"])
        self.assertEqual(out["human_reason"], "HIGH_RISK")


if __name__ == "__main__":
    unittest.main()

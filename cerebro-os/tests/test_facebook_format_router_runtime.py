import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from facebook_format_router import (
    CURRENT_ROUTER_ID,
    HISTORICAL_ROUTER_IDS,
    FacebookFormatRouteRequest,
    historical_router_can_retire,
    route_facebook_format,
)


class FacebookFormatRouterTests(unittest.TestCase):
    def request(self, **overrides):
        data = dict(
            company_id="fenix-capital",
            engine_id="MKT-ROUTER-FB",
            environment="TEST",
            version="1.0.0",
            publication_id="pub-1",
            run_id="run-1",
            format="Imagen",
        )
        data.update(overrides)
        return FacebookFormatRouteRequest(**data)

    def test_all_v4_formats_route_without_external_action(self):
        expected = {
            "Texto orgánico simple": 9533715,
            "Texto + enlace": 9533724,
            "Imagen": 9533532,
            "Vídeo corto": 9533564,
            "Carrusel": 9533967,
            "Vídeo largo": 9533972,
            "Story": 9533976,
        }
        for fmt, target in expected.items():
            with self.subTest(fmt=fmt):
                out = route_facebook_format(self.request(format=fmt))
                self.assertEqual(out["status"], "ROUTED")
                self.assertEqual(out["target_scenario_id"], target)
                self.assertEqual(out["router_scenario_id"], CURRENT_ROUTER_ID)
                self.assertEqual(out["platform_state"], "FACEBOOK_NOT_CALLED")
                self.assertFalse(out["external_action_allowed"])
                self.assertFalse(out["requires_human"])

    def test_unknown_format_fails_closed(self):
        out = route_facebook_format(self.request(format="Formato inventado"))
        self.assertEqual(out["status"], "BLOCKED_UNKNOWN_FORMAT")
        self.assertTrue(out["requires_human"])
        self.assertEqual(out["human_reason"], "LOW_CONFIDENCE")
        self.assertFalse(out["external_action_allowed"])

    def test_historical_router_ids_are_registered(self):
        self.assertEqual(
            HISTORICAL_ROUTER_IDS,
            frozenset({9528432, 9530604, 9531140, 9533487, 9533499}),
        )

    def test_retirement_is_fail_closed(self):
        self.assertTrue(historical_router_can_retire(
            scenario_id=9530604,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=True,
            target_runtime_live=True,
        ))
        self.assertFalse(historical_router_can_retire(
            scenario_id=9530604,
            caller_map_complete=True,
            replay_parity_green=True,
            rollback_proven=False,
            target_runtime_live=True,
        ))
        with self.assertRaises(ValueError):
            historical_router_can_retire(
                scenario_id=123,
                caller_map_complete=True,
                replay_parity_green=True,
                rollback_proven=True,
                target_runtime_live=True,
            )


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))

from facebook_caller_map import FACEBOOK_V3_TARGETS, get_target, router_references_superseded_legacy


class FacebookCallerMapTests(unittest.TestCase):
    def test_v3_router_does_not_reference_superseded_legacy(self):
        self.assertFalse(router_references_superseded_legacy())

    def test_expected_replacements_are_mapped(self):
        self.assertEqual(get_target("Texto orgánico simple").target_scenario_id, 9530484)
        self.assertEqual(get_target("Texto + enlace").target_scenario_id, 9531078)
        self.assertEqual(get_target("Imagen").target_scenario_id, 9531133)
        self.assertEqual(get_target("Vídeo corto").target_scenario_id, 9533424)
        self.assertTrue(all(not target.external_action_allowed for target in FACEBOOK_V3_TARGETS.values()))

    def test_unknown_format_fails_closed(self):
        with self.assertRaises(ValueError):
            get_target("Formato inventado")


if __name__ == "__main__":
    unittest.main()

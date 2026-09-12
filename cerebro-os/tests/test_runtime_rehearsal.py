import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))

from runtime_rehearsal import run_rehearsal


class RuntimeRehearsalTests(unittest.TestCase):
    def test_rehearsal_is_green(self):
        result = run_rehearsal()
        self.assertTrue(result.boot_green)
        self.assertTrue(result.route_map_green)
        self.assertTrue(result.rollback_trigger_green)
        self.assertTrue(result.external_action_safe)
        self.assertTrue(result.green)


if __name__ == "__main__":
    unittest.main()

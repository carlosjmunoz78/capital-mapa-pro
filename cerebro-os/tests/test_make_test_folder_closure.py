import json
import os
import unittest

HERE = os.path.dirname(__file__)
FIXTURE = os.path.abspath(os.path.join(HERE, "..", "runtime", "fixtures", "make_test_folder_closure_2026-09-12.json"))


class MakeTestFolderClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIXTURE, "r", encoding="utf-8") as fh:
            cls.data = json.load(fh)

    def test_total_count_is_exhaustive(self):
        d = self.data
        self.assertEqual(len(d["active_ids"]), 2)
        self.assertEqual(len(d["error_ids"]), 1)
        self.assertEqual(sum(d["inactive_partition"].values()), d["inactive_count"])
        self.assertEqual(len(d["active_ids"]) + len(d["error_ids"]) + d["inactive_count"], d["scenario_count"])
        self.assertEqual(d["scenario_count"], 120)

    def test_fenix_test_partition_is_62(self):
        self.assertEqual(sum(self.data["fenix_test_subfamilies"].values()), 62)
        self.assertEqual(self.data["inactive_partition"]["FENIX_TEST"], 62)

    def test_safety_is_fail_closed(self):
        safety = self.data["safety"]
        self.assertFalse(safety["delete_allowed"])
        self.assertFalse(safety["auto_activate_inactive_allowed"])
        self.assertFalse(safety["external_action_allowed"])
        self.assertTrue(safety["preserve_active_edges"])


if __name__ == "__main__":
    unittest.main()

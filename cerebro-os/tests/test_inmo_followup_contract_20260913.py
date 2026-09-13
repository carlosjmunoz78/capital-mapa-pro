import pathlib
import runpy
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class T(unittest.TestCase):
    def test_contract(self):
        ns = runpy.run_path(str(ROOT / "runtime" / "inmo_followup_semantic_replay_20260913.py"))
        r = ns["assess"]()
        self.assertTrue(r["lab_green"])
        self.assertFalse(r["real_db_replay"])
        self.assertFalse(r["rollback_proven"])


if __name__ == "__main__":
    unittest.main()

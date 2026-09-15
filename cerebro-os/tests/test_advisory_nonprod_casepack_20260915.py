import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from advisory.nonprod_casepack import (
    CASE_PACK_ENTRIES,
    CASE_PACK_VERSION,
    case_pack_sha256,
    verify_case_pack,
)
from advisory.models import CANONICAL_DOMAINS

EXPECTED_SHA256 = "2f7667de19bffaf8c1dca52837268e51ca44b849a60d6ce7235055920cf1e63d"


class AdvisoryNonProdCasePackTests(unittest.TestCase):
    def test_case_pack_identity_is_immutable(self):
        self.assertEqual(CASE_PACK_VERSION, "1.0.0")
        self.assertEqual(case_pack_sha256(), EXPECTED_SHA256)
        self.assertTrue(verify_case_pack(EXPECTED_SHA256))

    def test_case_pack_is_nonempty_and_green_expected(self):
        self.assertEqual(len(CASE_PACK_ENTRIES), 3)
        self.assertTrue(all(entry.expected_status == "GREEN" for entry in CASE_PACK_ENTRIES))

    def test_case_pack_jointly_covers_all_domains(self):
        covered = {domain for entry in CASE_PACK_ENTRIES for domain in entry.domains}
        self.assertEqual(covered, set(CANONICAL_DOMAINS))


if __name__ == "__main__":
    unittest.main()

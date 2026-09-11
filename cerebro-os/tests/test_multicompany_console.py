import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "multicompany"))
sys.path.insert(0, str(ROOT / "console"))

from company_registry import CompanyRecord
from command import ConsoleCommand


class MultiCompanyConsoleTests(unittest.TestCase):
    def test_company_record_validates(self):
        record = CompanyRecord(company_id="fenix-capital", legal_name="Fénix Capital")
        record.validate()

    def test_invalid_company_state_rejected(self):
        record = CompanyRecord(company_id="x", legal_name="X", state="INVALID")
        with self.assertRaises(ValueError):
            record.validate()

    def test_console_requires_company_context(self):
        command = ConsoleCommand(user_id="u1", company_id="fenix-capital", context_type="global", context_id=None, message="estado")
        command.validate()
        self.assertTrue(command.request_id)

    def test_console_rejects_missing_company(self):
        command = ConsoleCommand(user_id="u1", company_id="", context_type="global", context_id=None, message="estado")
        with self.assertRaises(ValueError):
            command.validate()


if __name__ == "__main__":
    unittest.main()

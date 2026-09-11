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
        record = CompanyRecord(company_id="fenix-capital", legal_name="Fénix Capital", environment="PROD", version="2.0.0")
        record.validate()

    def test_invalid_company_identity_scope_or_state_rejected(self):
        for record in (
            CompanyRecord(company_id="x", legal_name="X", state="INVALID"),
            CompanyRecord(company_id="", legal_name="X"),
            CompanyRecord(company_id="x", legal_name=""),
            CompanyRecord(company_id="x", legal_name="X", version=""),
            CompanyRecord(company_id="x", legal_name="X", environment="DEV"),
        ):
            with self.assertRaises(ValueError):
                record.validate()

    def test_console_requires_company_context(self):
        command = ConsoleCommand(user_id="u1", company_id="fenix-capital", context_type="global", context_id=None, message="estado")
        command.validate()
        self.assertTrue(command.request_id)
        self.assertEqual("LAB", command.environment)
        self.assertEqual("1.0.0", command.version)

    def test_console_rejects_missing_company(self):
        command = ConsoleCommand(user_id="u1", company_id="", context_type="global", context_id=None, message="estado")
        with self.assertRaises(ValueError):
            command.validate()

    def test_console_rejects_invalid_environment_or_missing_version(self):
        with self.assertRaises(ValueError):
            ConsoleCommand(user_id="u1", company_id="fenix-capital", context_type="global", context_id=None, message="estado", environment="DEV").validate()
        with self.assertRaises(ValueError):
            ConsoleCommand(user_id="u1", company_id="fenix-capital", context_type="global", context_id=None, message="estado", version="").validate()


if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest

HERE = os.path.dirname(__file__)
CONSOLE = os.path.abspath(os.path.join(HERE, "..", "console"))
if CONSOLE not in sys.path:
    sys.path.insert(0, CONSOLE)

from pipeline import ConsolePipeline


class ConsoleV0GatewayPathTests(unittest.TestCase):
    def base_command(self, **overrides):
        command = {
            "request_id": "req-1",
            "user_id": "user-1",
            "company_id": "fenix",
            "context_type": "company",
            "message": "estado motores",
            "environment": "LAB",
            "version": "1.0.0",
        }
        command.update(overrides)
        return command

    def test_console_always_routes_through_gateway_and_audits(self):
        audits = []
        def gateway(command):
            return {
                "status": "ROUTED",
                "company_id": command["company_id"],
                "environment": command["environment"],
                "version": command["version"],
                "engine_id": "STATUS-001",
            }
        out = ConsolePipeline(gateway, audits.append).execute(self.base_command())
        self.assertEqual(out["path"], ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"))
        self.assertEqual(out["status"], "ROUTED")
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["company_id"], "fenix")

    def test_cross_company_gateway_result_is_rejected(self):
        def gateway(command):
            return {"status": "ROUTED", "company_id": "other-company"}
        with self.assertRaises(ValueError):
            ConsolePipeline(gateway, lambda _: None).execute(self.base_command())

    def test_environment_scope_mismatch_is_rejected(self):
        def gateway(command):
            return {"status": "ROUTED", "environment": "PROD"}
        with self.assertRaises(ValueError):
            ConsolePipeline(gateway, lambda _: None).execute(self.base_command(environment="LAB"))

    def test_invalid_environment_fails_before_gateway(self):
        calls = []
        with self.assertRaises(ValueError):
            ConsolePipeline(lambda command: calls.append(command), lambda _: None).execute(self.base_command(environment="INVALID"))
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()

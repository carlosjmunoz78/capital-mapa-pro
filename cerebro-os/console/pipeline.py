from __future__ import annotations

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


class ConsolePipeline:
    def __init__(self, gateway_route, audit_sink):
        if not callable(gateway_route) or not callable(audit_sink):
            raise ValueError("gateway_route and audit_sink must be callable")
        self.gateway_route = gateway_route
        self.audit_sink = audit_sink

    def execute(self, command: dict) -> dict:
        required = (
            "request_id", "user_id", "company_id", "context_type", "message",
            "environment", "version",
        )
        missing = tuple(key for key in required if not command.get(key))
        if missing:
            raise ValueError(f"missing console command fields: {missing}")
        if command["environment"] not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")

        routed = self.gateway_route(command)
        if not isinstance(routed, dict) or "status" not in routed:
            raise ValueError("gateway must return a status-bearing dict")

        if routed.get("company_id") not in {None, command["company_id"]}:
            raise ValueError("gateway company scope mismatch")
        if routed.get("environment") not in {None, command["environment"]}:
            raise ValueError("gateway environment scope mismatch")
        if routed.get("version") not in {None, command["version"]}:
            raise ValueError("gateway version scope mismatch")

        audit = {
            "request_id": command["request_id"],
            "user_id": command["user_id"],
            "company_id": command["company_id"],
            "context_type": command["context_type"],
            "environment": command["environment"],
            "version": command["version"],
            "gateway_status": routed["status"],
        }
        self.audit_sink(audit)
        return {
            "request_id": command["request_id"],
            "company_id": command["company_id"],
            "environment": command["environment"],
            "version": command["version"],
            "status": routed["status"],
            "gateway_result": routed,
            "path": ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"),
        }

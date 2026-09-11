from __future__ import annotations


class ConsolePipeline:
    def __init__(self, gateway_route, audit_sink):
        if not callable(gateway_route) or not callable(audit_sink):
            raise ValueError("gateway_route and audit_sink must be callable")
        self.gateway_route = gateway_route
        self.audit_sink = audit_sink

    def execute(self, command: dict) -> dict:
        required = ("request_id", "user_id", "company_id", "context_type", "message")
        missing = tuple(key for key in required if not command.get(key))
        if missing:
            raise ValueError(f"missing console command fields: {missing}")
        routed = self.gateway_route(command)
        if not isinstance(routed, dict) or "status" not in routed:
            raise ValueError("gateway must return a status-bearing dict")
        audit = {
            "request_id": command["request_id"],
            "user_id": command["user_id"],
            "company_id": command["company_id"],
            "context_type": command["context_type"],
            "gateway_status": routed["status"],
        }
        self.audit_sink(audit)
        return {
            "request_id": command["request_id"],
            "company_id": command["company_id"],
            "status": routed["status"],
            "gateway_result": routed,
            "path": ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"),
        }

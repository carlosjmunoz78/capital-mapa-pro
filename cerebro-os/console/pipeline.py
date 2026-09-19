from __future__ import annotations

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


class ConsolePipeline:
    def __init__(self, gateway_route, audit_sink, engine_execute=None):
        if not callable(gateway_route) or not callable(audit_sink):
            raise ValueError("gateway_route and audit_sink must be callable")
        if engine_execute is not None and not callable(engine_execute):
            raise ValueError("engine_execute must be callable")
        self.gateway_route = gateway_route
        self.audit_sink = audit_sink
        self.engine_execute = engine_execute

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

        engine_result=None
        if routed.get("status")=="ROUTED" and self.engine_execute is not None:
            engine_result=self.engine_execute(dict(command),dict(routed))
            if not isinstance(engine_result,dict) or "status" not in engine_result:
                raise ValueError("engine_execute must return a status-bearing dict")
            if engine_result.get("company_id") not in {None, command["company_id"]}:
                raise ValueError("engine result company scope mismatch")
            if engine_result.get("environment") not in {None, command["environment"]}:
                raise ValueError("engine result environment scope mismatch")
            if engine_result.get("version") not in {None, command["version"]}:
                raise ValueError("engine result version scope mismatch")
            if engine_result.get("engine_id") not in {None, routed.get("engine_id")}:
                raise ValueError("engine result engine scope mismatch")

        final_status=engine_result["status"] if engine_result is not None else routed["status"]
        audit = {
            "request_id": command["request_id"],
            "user_id": command["user_id"],
            "company_id": command["company_id"],
            "context_type": command["context_type"],
            "environment": command["environment"],
            "version": command["version"],
            "gateway_status": routed["status"],
            "engine_id": routed.get("engine_id"),
            "engine_status": engine_result.get("status") if engine_result else None,
        }
        self.audit_sink(audit)
        return {
            "request_id": command["request_id"],
            "company_id": command["company_id"],
            "environment": command["environment"],
            "version": command["version"],
            "status": final_status,
            "gateway_result": routed,
            "engine_result": engine_result,
            "execution_mode": "EXECUTED" if engine_result is not None else "ROUTE_ONLY",
            "path": ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"),
        }

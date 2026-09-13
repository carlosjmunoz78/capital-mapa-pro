from __future__ import annotations

AUDIT = {
    "captured_at": "2026-09-13",
    "mode": "READ_ONLY",
    "app_main_sha": "95106d8e792257f809033486b7025d81665ea83b",
    "APP_009_carlos_access": {
        "status": "PROFILE_SURFACE_FOUND_LINK_DEPENDENCY_OPEN",
        "profile_route": "/perfil",
        "profile_shell_present": True,
        "profile_launcher_present": True,
        "profile_launcher_targets": (".avatar", ".ops-profile"),
        "profile_data_via_app_gateway": True,
        "cerebro_link_present": False,
        "cerebro_web_route_present": False,
        "safe_to_add_dead_link": False,
        "reason": "CEREBRO console has logical contracts but no deployable App web route evidenced yet.",
    },
    "APP_010_cerebro_gateway": {
        "status": "LOGICAL_CONTRACT_GREEN_DEPLOYABLE_HTTP_SURFACE_MISSING",
        "gateway_request_scopes": ("user_id", "company_id", "context", "command", "request_id", "environment", "version"),
        "valid_environments": ("LAB", "PREPROD", "PROD"),
        "unknown_command_fail_closed": ("HUMAN_REQUIRED", "LOW_CONFIDENCE"),
        "pipeline_path": ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"),
        "audit_sink_required": True,
        "company_scope_enforced": True,
        "environment_scope_enforced": True,
        "version_scope_enforced": True,
        "console_session_contract_present": True,
        "command_classification_present": True,
        "action_policy_and_iam_gates_present": True,
        "direct_model_path_present": False,
        "deployable_http_or_app_route_evidenced": False,
    },
}


def assess() -> dict:
    access = AUDIT["APP_009_carlos_access"]
    gateway = AUDIT["APP_010_cerebro_gateway"]
    logical_gateway_green = all((
        gateway["audit_sink_required"],
        gateway["company_scope_enforced"],
        gateway["environment_scope_enforced"],
        gateway["version_scope_enforced"],
        gateway["console_session_contract_present"],
        gateway["command_classification_present"],
        gateway["action_policy_and_iam_gates_present"],
        not gateway["direct_model_path_present"],
    ))
    return {
        "APP_009_profile_surface_green": access["profile_shell_present"] and access["profile_launcher_present"],
        "APP_009_cerebro_link_green": access["cerebro_link_present"] and access["cerebro_web_route_present"],
        "APP_010_logical_gateway_green": logical_gateway_green,
        "APP_010_deployable_surface_green": gateway["deployable_http_or_app_route_evidenced"],
        "safe_to_add_cerebro_profile_link_now": access["safe_to_add_dead_link"],
        "safe_next": "build_deployable_console_surface_behind_cerebro_gateway_then_add_carlos_profile_link_on_parallel_app_branch",
        "status": "CONSOLE_GATEWAY_LOGICAL_GREEN_DEPLOYABLE_SURFACE_REQUIRED",
    }

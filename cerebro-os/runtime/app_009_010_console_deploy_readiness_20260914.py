from __future__ import annotations

READINESS = {
    "captured_at": "2026-09-14",
    "mode": "SAFE_PARALLEL_READINESS",
    "APP_009": {
        "profile_route": "/perfil",
        "profile_shell_present": True,
        "console_route": "/cerebro",
        "profile_link_must_be_feature_gated": True,
        "console_url_evidenced": False,
        "dead_link_allowed": False,
    },
    "APP_010": {
        "http_surface_implemented": True,
        "http_routes": ("/health", "/companies", "/commands"),
        "identity_source": "TRUSTED_UPSTREAM_REMOTE_USER_OR_RESOLVER",
        "browser_identity_header_trusted": False,
        "identity_in_json_body_allowed": False,
        "pipeline": ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT"),
        "direct_model_path_present": False,
        "web_ui_surface_evidenced": True,
        "web_ui_route": "/cerebro",
        "web_ui_fail_closed_until_gateway_url": True,
        "deployed_url_evidenced": False,
        "production_promotion_allowed": False,
    },
}


def assess() -> dict:
    app = READINESS["APP_009"]
    console = READINESS["APP_010"]
    contract_green = (
        console["http_surface_implemented"]
        and console["http_routes"] == ("/health", "/companies", "/commands")
        and console["identity_source"] == "TRUSTED_UPSTREAM_REMOTE_USER_OR_RESOLVER"
        and not console["browser_identity_header_trusted"]
        and not console["identity_in_json_body_allowed"]
        and console["pipeline"] == ("CONSOLE", "GATEWAY", "POLICY", "ENGINE", "AUDIT")
        and not console["direct_model_path_present"]
    )
    web_ui_green = bool(console["web_ui_surface_evidenced"] and console["web_ui_route"] == "/cerebro" and console["web_ui_fail_closed_until_gateway_url"])
    deployable_green = contract_green and web_ui_green and console["deployed_url_evidenced"]
    safe_profile_link = bool(app["profile_link_must_be_feature_gated"] and app["console_url_evidenced"] and deployable_green)
    return {
        "APP_010_http_contract_green": contract_green,
        "APP_010_web_ui_green": web_ui_green,
        "APP_010_deployable_green": deployable_green,
        "APP_009_profile_link_ready": safe_profile_link,
        "production_promotion_allowed": bool(console["production_promotion_allowed"] and deployable_green),
        "safe_next": "deploy_authenticated_console_gateway_url_then_enable_profile_link_by_explicit_https_config",
        "status": "HTTP_AND_WEB_UI_GREEN_DEPLOYED_URL_OPEN",
    }

from __future__ import annotations

EVIDENCE = {
    "app_repo": "carlosjmunoz78/fenix-capital-inmo-map",
    "approved_branch_sha": "b1b6fb5404a4704c5d637fc770fc90e9f2eb8312",
    "main_merge_sha": "dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c",
    "prod_deploy_run": 34790008072,
    "prod_deploy_success": True,
    "gh_pages_commit": "c8a4bc720ce91eb46ed811c506623c265d043594",
    "prod_source_sha_matches_main": True,
    "main_direct_prod_rpc_search_zero": True,
    "gateway_version": 17,
    "gateway_http_health_200": True,
    "gateway_unauthenticated_target_route_401": True,
    "authenticated_http_e2e_proven": False,
    "http_write_path_rollback_proven": False,
    "legacy_retirement_sql_prepared": True,
    "legacy_retirement_applied": False,
    "cloudflare_workers_builds_success": True,
    "cloudflare_pages_parallel_check_green": False,
    "cloudflare_pages_routing_role_proven": False,
}


def assess() -> dict:
    source_promotion_green = all(
        EVIDENCE[k]
        for k in (
            "prod_deploy_success",
            "prod_source_sha_matches_main",
            "main_direct_prod_rpc_search_zero",
            "gateway_http_health_200",
            "gateway_unauthenticated_target_route_401",
        )
    )
    retirement_allowed = bool(
        source_promotion_green
        and EVIDENCE["authenticated_http_e2e_proven"]
        and EVIDENCE["http_write_path_rollback_proven"]
    )
    security_green = bool(
        retirement_allowed
        and EVIDENCE["legacy_retirement_applied"]
        and EVIDENCE["cloudflare_pages_parallel_check_green"]
    )
    return {
        "source_promotion_green": source_promotion_green,
        "authenticated_http_e2e_proven": EVIDENCE["authenticated_http_e2e_proven"],
        "http_write_path_rollback_proven": EVIDENCE["http_write_path_rollback_proven"],
        "legacy_retirement_allowed": retirement_allowed,
        "legacy_retirement_applied": EVIDENCE["legacy_retirement_applied"],
        "cloudflare_topology_closed": bool(
            EVIDENCE["cloudflare_pages_parallel_check_green"]
            or EVIDENCE["cloudflare_pages_routing_role_proven"]
        ),
        "security_green": security_green,
        "status": "SOURCE_PROMOTION_GREEN_HTTP_AUTH_E2E_OPEN" if source_promotion_green and not security_green else "SECURITY_GREEN",
    }

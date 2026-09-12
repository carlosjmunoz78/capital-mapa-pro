from __future__ import annotations

LEGACY_PROJECT_ID = "hnqlnvakzaywtafeiybt"

NOTION = {
    "deprecated_bridge": {
        "slug": "fenix-notion-bridge",
        "status": "ACTIVE",
        "version": 12,
        "runtime_contract": "HTTP_410_DEPRECATED_REPLACED_BY_FENIX_MAKE_REDES",
    },
    "runtime_test": {
        "slug": "fenix-notion-runtime-test",
        "status": "ACTIVE",
        "version": 10,
        "environment": "PREPROD_TEST",
        "mode": "READ_ONLY_CANONICAL_NOTION_RUNTIME",
        "pagination": "FULL",
        "canonical_source": "notion_canonical",
    },
}

WORDPRESS = {
    "preprod_probe": {
        "slug": "fenix-wordpress-preprod",
        "status": "ACTIVE",
        "version": 7,
        "base": "https://fenixcapital.es",
        "fixture_status": "draft",
        "publish_allowed": False,
        "rollback_mode_present": True,
    }
}

SEO = {
    "executor_preprod": {
        "slug": "fenix-seo-executor-preprod",
        "status": "ACTIVE",
        "version": 7,
        "environment": "PREPROD",
        "allowed_fields": ("title", "excerpt"),
        "published_target_blocked": True,
        "dry_run_supported": True,
        "post_write_verification": True,
        "rollback_on_verification_failure": True,
    },
    "make_prod_gsc_edges": (9597710, 9550706),
}


def assess_live_map() -> dict:
    notion_live = NOTION["runtime_test"]["status"] == "ACTIVE"
    wp_live = WORDPRESS["preprod_probe"]["status"] == "ACTIVE"
    seo_live = SEO["executor_preprod"]["status"] == "ACTIVE" and len(SEO["make_prod_gsc_edges"]) == 2
    return {
        "legacy_project_id": LEGACY_PROJECT_ID,
        "notion_live_verified": notion_live,
        "notion_old_bridge_fail_closed": NOTION["deprecated_bridge"]["runtime_contract"].startswith("HTTP_410"),
        "wordpress_preprod_live_verified": wp_live,
        "wordpress_prod_publish_exercised": False,
        "seo_preprod_executor_live_verified": SEO["executor_preprod"]["status"] == "ACTIVE",
        "seo_prod_read_only_edges_verified": len(SEO["make_prod_gsc_edges"]) == 2,
        "all_dependency_edges_live_verified": notion_live and wp_live and seo_live,
        "prod_mutation_performed": False,
        "prod_candidate_allowed": False,
        "status": "LIVE_NOTION_WORDPRESS_SEO_MAP_VERIFIED_PROD_WRITE_GATED" if notion_live and wp_live and seo_live else "LIVE_NOTION_WORDPRESS_SEO_MAP_BLOCKED",
    }

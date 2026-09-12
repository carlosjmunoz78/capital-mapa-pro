from runtime.facebook_format_router import FacebookFormatRouteRequest, route_facebook_format
from runtime.linkedin_preflight import LinkedInPreflightRequest, plan_linkedin_preflight
from runtime.youtube_preflight import YouTubePreflightRequest, plan_youtube_preflight


def test_facebook_v4_make_routes_match_native_runtime_targets():
    expected = {
        "Texto orgánico simple": 9533715,
        "Texto + enlace": 9533724,
        "Imagen": 9533532,
        "Vídeo corto": 9533564,
        "Carrusel": 9533967,
        "Vídeo largo": 9533972,
        "Story": 9533976,
    }
    for fmt, target in expected.items():
        result = route_facebook_format(FacebookFormatRouteRequest(
            company_id="fenix", engine_id="facebook", environment="LAB", version="V4",
            publication_id="pub-1", run_id="run-1", format=fmt,
        ))
        assert result["status"] == "ROUTED"
        assert result["target_scenario_id"] == target
        assert result["platform_state"] == "FACEBOOK_NOT_CALLED"
        assert result["external_action_allowed"] is False


def test_linkedin_make_text_contract_matches_native_preflight():
    result = plan_linkedin_preflight(LinkedInPreflightRequest(
        company_id="fenix", engine_id="linkedin", environment="LAB", version="V1",
        publication_id="pub-li", run_id="run-li", format="texto",
        content_ready=True, asset_ready=False, url_ready=False,
        qa_passed=True, schedule_ready=True, duplicate_exists=False,
    ))
    assert result["status"] == "ROUTED_WITH_PUBLISH_ENGINE_DISABLED"
    assert result["preflight_status"] == "PREFLIGHT_READY"
    assert result["operation_type"] == "route_texto"
    assert result["platform_state"] == "LINKEDIN_NOT_CALLED"
    assert result["external_action_allowed"] is False
    assert result["requires_human"] is True


def test_linkedin_make_format_specific_gates_and_duplicate_block_are_preserved():
    blocked_link = plan_linkedin_preflight(LinkedInPreflightRequest(
        company_id="fenix", engine_id="linkedin", environment="LAB", version="V1",
        publication_id="pub-li", run_id="run-li", format="enlace",
        content_ready=True, asset_ready=False, url_ready=False,
        qa_passed=True, schedule_ready=True, duplicate_exists=False,
    ))
    assert blocked_link["status"] == "BLOCKED_PREFLIGHT"
    duplicate = plan_linkedin_preflight(LinkedInPreflightRequest(
        company_id="fenix", engine_id="linkedin", environment="LAB", version="V1",
        publication_id="pub-li", run_id="run-li", format="imagen",
        content_ready=True, asset_ready=True, url_ready=False,
        qa_passed=True, schedule_ready=True, duplicate_exists=True,
    ))
    assert duplicate["status"] == "BLOCKED_DUPLICATE"
    assert duplicate["external_action_allowed"] is False


def test_youtube_make_contract_matches_native_preflight_and_channel_gate():
    result = plan_youtube_preflight(YouTubePreflightRequest(
        company_id="fenix", engine_id="youtube", environment="LAB", version="V1",
        publication_id="pub-yt", run_id="run-yt", format="short",
        channel_id="UC0XL5bW9A6vXfNc5EDIN0Ig", privacy_status="private",
        content_ready=True, asset_ready=True, qa_passed=True, schedule_ready=True,
        duplicate_exists=False,
    ))
    assert result["status"] == "ROUTED_WITH_ENGINE_DISABLED"
    assert result["preflight_status"] == "PREFLIGHT_READY_PUBLISH_BLOCKED"
    assert result["post_video_id_steps"] == ["thumbnail", "playlist", "captions", "processing"]
    assert result["platform_state"] == "YOUTUBE_NOT_CALLED"
    assert result["external_action_allowed"] is False

    wrong_channel = plan_youtube_preflight(YouTubePreflightRequest(
        company_id="fenix", engine_id="youtube", environment="LAB", version="V1",
        publication_id="pub-yt", run_id="run-yt", format="short",
        channel_id="wrong", privacy_status="private",
        content_ready=True, asset_ready=True, qa_passed=True, schedule_ready=True,
        duplicate_exists=False,
    ))
    assert wrong_channel["status"] == "BLOCKED_WRONG_CHANNEL"
    assert wrong_channel["external_action_allowed"] is False

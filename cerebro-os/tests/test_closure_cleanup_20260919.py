from pathlib import Path

GROUPS=Path("cerebro-os/runtime/closure_objective_groups.py").read_text()
MASTER=Path("cerebro-os/evidence/CEREBRO_OS_CIERRE_MAESTRO_20260918.md").read_text()

def test_security_closure_has_no_stale_search_path_remaining_marker():
    assert "two_mutable_search_path_function_warnings_disposition" not in GROUPS
    assert "two_mutable_search_path_warnings_closed_2026_09_16" in GROUPS
    assert "session_context_zero_known_active_edge_direct_callers_2026_09_19" in GROUPS

def test_latest_preprod_evidence_is_registered():
    assert "forge_preprod_43_persistent_observability_success_2026_09_19" in GROUPS
    assert "10571531192" in MASTER
    assert "8432411f36be5937ffb773de3a5e0f4548aecae1b7d9bb008c19da3578384c91" in MASTER


def test_app_session_context_source_sync_closure_is_registered():
    assert "session_context_app_pr_414_merged_main_c17064ca_2026_09_19" in GROUPS
    assert "session_context_regression_guard_10_postmerge_zero_direct_repo_callers_2026_09_19" in GROUPS
    assert "c17064ca90adc6c29b63f2810f6e7dfb848ad407" in MASTER
    assert "App Restoration Build Gate #289: SUCCESS" in MASTER
    assert "PROD Runtime Smoke #258: SUCCESS" in MASTER

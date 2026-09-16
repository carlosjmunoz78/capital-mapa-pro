from pathlib import Path


def _evidence() -> str:
    return Path("cerebro-os/evidence/security/SUPABASE_PROD_AUTH_SECDEF_CALLER_MAP_20260916.md").read_text()


def test_session_context_retirement_is_blocked_by_newly_discovered_live_callers():
    evidence = _evidence()
    for name in (
        "fenix-ana-canonical",
        "fenix-memory-api",
        "fenix-evidence-api",
        "fenix-ana-api",
    ):
        assert name in evidence
    assert "RETIREMENT_BLOCKED_ADDITIONAL_LIVE_CALLERS_DISCOVERED" in evidence
    assert "MUST NOT be revoked yet" in evidence


def test_previously_known_callers_are_recorded_as_migrated_in_prod():
    evidence = _evidence()
    assert "fenix-ana-knowledge` v10 · MIGRATED IN PROD" in evidence
    assert "fenix-b2b-actions` v10 · MIGRATED IN PROD" in evidence
    assert "057dc41b86de5a3dcc059f58249dde16424e1b19937ead891f2bfebf5e610884" in evidence
    assert "970beb8876a3ad657124fc28038cb040a42d3fa8ffd9f2ee2bcc07ce6ec66ce2" in evidence


def test_server_identity_pattern_is_recorded_for_inspected_clean_edge_surfaces():
    evidence = _evidence()
    for name in (
        "fenix-directory-actions",
        "fenix-task-actions",
        "fenix-expediente-actions",
        "fenix-directory-api",
        "fenix-economia-api",
        "fenix-task-api",
        "fenix-bank-api",
        "fenix-reports-api",
    ):
        assert name in evidence
    assert "fenix_prod_actor_context_by_auth_server" in evidence


def test_caller_map_keeps_e2e_external_callers_and_global_green_fail_closed():
    evidence = _evidence()
    assert "authenticated HTTP E2E" in evidence
    assert "External/direct REST/RPC caller absence remains `POR_AUDITAR`" in evidence
    assert "No bulk revoke" in evidence or "no bulk revoke" in evidence
    assert "do not grant SECURITY green" in evidence
    assert "16 `authenticated_security_definer_function_executable`" in evidence

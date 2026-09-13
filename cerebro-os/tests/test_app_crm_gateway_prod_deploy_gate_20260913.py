import json
from pathlib import Path


def load_evidence():
    path = Path(__file__).resolve().parents[1] / "evidence" / "app_crm_gateway_prod_deploy_gate_20260913.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_gateway_prod_deploy_gate_fails_closed():
    e = load_evidence()
    assert e["status"] == "PARTIAL_FAIL_CLOSED"
    assert e["edge_function"]["prod_status"] == "ACTIVE"
    assert e["edge_function"]["prod_version"] == 16
    assert e["edge_function"]["custom_auth_preserved"] is True
    assert e["edge_function"]["prod_contains_new_8_routes"] is False
    assert e["migration_branch"]["persisted_direct_prod_rpc_callers"] == 0
    assert e["migration_branch"]["required_gateway_routes"] == 8
    assert e["migration_branch"]["ci_conclusion"] == "success"
    assert e["prod_contracts"]["server_wrappers_5_of_5"] is True
    assert e["latest_deploy_attempt"]["executed"] is False
    assert e["latest_deploy_attempt"]["partial_prod_change"] is False
    assert e["gates"]["legacy_execute_revoke_allowed"] is False
    assert e["gates"]["merge_to_main_allowed"] is False


def test_gateway_prod_deploy_gate_keeps_required_sequence():
    e = load_evidence()
    seq = e["required_next_sequence"]
    assert seq[0] == "deploy_gateway_prod"
    assert "verify_successful_write_paths_with_rollback" in seq
    assert seq[-1] == "human_gate_before_permission_retirement_or_main_promotion"

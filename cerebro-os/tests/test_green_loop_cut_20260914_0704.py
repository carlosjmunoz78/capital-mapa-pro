from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "green_loop_cut_20260914_0704.py"
spec = importlib.util.spec_from_file_location("green_loop_cut_20260914_0704", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def test_app_prod_runtime_is_exact_sha_green():
    row = mod.CUT["app_prod"]
    assert row["main_sha"] == "dd09153a6d025d9cc75eb2c14e776a9e5bd8e16c"
    assert row["prod_live_deploy_green"] is True
    assert row["prod_runtime_smoke_green"] is True
    assert row["live_exact_sha_green"] is True
    assert row["prod_only_backend_binding_green"] is True
    assert row["gateway_health_green"] is True
    assert row["anonymous_gateway_fail_closed_green"] is True


def test_security_stays_fail_closed_until_safe_authenticated_e2e():
    row = mod.CUT["security"]
    assert row["source_promotion_green"] is True
    assert row["target_callers_zero_green"] is True
    assert row["rls_no_policy_info_count"] == 44
    assert row["security_definer_authenticated_warn_count"] == 24
    assert row["security_definer_migrated_legacy_targets"] == 8
    assert row["security_definer_read_session_surfaces"] == 7
    assert row["security_definer_mutators_review_required"] == 9
    assert row["security_definer_partition_complete"] is True
    assert row["cloudflare_pages_failure_blocks_app_runtime"] is False
    assert row["cloudflare_pages_resource_mutation_allowed"] is False
    assert row["authenticated_http_e2e_green"] is False
    assert row["http_write_rollback_green"] is False
    assert row["legacy_execute_retirement_allowed"] is False
    assert row["human_required"] == "HIGH_RISK"


def test_recovery_app_source_rollback_is_green_but_provider_restore_stays_open():
    row = mod.CUT["recovery"]
    assert row["previous_prod_source_resolves"] is True
    assert row["rollback_rehearsal_workflow_present"] is True
    assert row["rollback_rehearsal_is_non_mutating"] is True
    assert row["rollback_rehearsal_run"] == 34808719859
    assert row["old_sha_rehearsal_green"] is True
    assert row["rollback_artifact_id"] == 10333274904
    assert row["rollback_artifact_sha256"] == "1d461022a00576a41acac8857af809aeff7666e0b4cdbd541f6fc67f6e4e787a"
    assert row["provider_restore_green"] is False
    assert row["paid_restore_resource_created"] is False


def test_finops_records_reference_without_inventing_invoice():
    row = mod.CUT["finops"]
    assert row["notion_current_reference_found"] is True
    assert row["notion_reference_usd_per_member_month"] == 20
    assert row["notion_reference_plan_label"] == "Business"
    assert row["notion_exact_current_invoice_eur_green"] is False
    assert row["google_cloud_payment_issue_evidence_found"] is True
    assert row["google_cloud_exact_monthly_amount_green"] is False
    assert row["estimated_unknown_costs_allowed"] is False


def test_global_promotion_remains_blocked():
    result = mod.assess()
    assert result["all_green"] is False
    assert set(result["pending"]) == {"security", "recovery", "observability", "finops", "promotion"}
    assert result["automatic_prod_promotion_allowed"] is False
    assert result["status"] == "GREEN_LOOP_IN_PROGRESS"

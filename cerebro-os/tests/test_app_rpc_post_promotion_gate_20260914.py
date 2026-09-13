from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "app_rpc_post_promotion_gate_20260914.py"
spec = importlib.util.spec_from_file_location("app_rpc_post_promotion_gate_20260914", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def test_source_promotion_is_green_but_security_is_still_fail_closed():
    row = mod.assess()
    assert row["source_promotion_green"] is True
    assert row["authenticated_http_e2e_proven"] is False
    assert row["http_write_path_rollback_proven"] is False
    assert row["legacy_retirement_allowed"] is False
    assert row["legacy_retirement_applied"] is False
    assert row["security_green"] is False
    assert row["status"] == "SOURCE_PROMOTION_GREEN_HTTP_AUTH_E2E_OPEN"


def test_retirement_cannot_be_allowed_by_source_provenance_alone(monkeypatch):
    monkeypatch.setitem(mod.EVIDENCE, "authenticated_http_e2e_proven", True)
    monkeypatch.setitem(mod.EVIDENCE, "http_write_path_rollback_proven", False)
    assert mod.assess()["legacy_retirement_allowed"] is False

    monkeypatch.setitem(mod.EVIDENCE, "authenticated_http_e2e_proven", False)
    monkeypatch.setitem(mod.EVIDENCE, "http_write_path_rollback_proven", True)
    assert mod.assess()["legacy_retirement_allowed"] is False


def test_cloudflare_parallel_failure_cannot_be_silently_promoted(monkeypatch):
    monkeypatch.setitem(mod.EVIDENCE, "authenticated_http_e2e_proven", True)
    monkeypatch.setitem(mod.EVIDENCE, "http_write_path_rollback_proven", True)
    monkeypatch.setitem(mod.EVIDENCE, "legacy_retirement_applied", True)
    monkeypatch.setitem(mod.EVIDENCE, "cloudflare_pages_parallel_check_green", False)
    monkeypatch.setitem(mod.EVIDENCE, "cloudflare_pages_routing_role_proven", False)
    row = mod.assess()
    assert row["cloudflare_topology_closed"] is False
    assert row["security_green"] is False

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "identity" / "credential_registry.py"
REGISTRY = ROOT / "identity" / "CREDENTIAL_REGISTRY_MAKE_2026-09-11.json"

spec = importlib.util.spec_from_file_location("credential_registry", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def test_registry_loads_and_never_contains_raw_secret_fields():
    registry = mod.CredentialRegistry.from_path(REGISTRY)
    assert registry.payload["policy"]["raw_secrets_in_git"] is False
    assert all(row["raw_value_stored_here"] is False for row in registry.payload["secrets"])


def test_known_connections_are_reusable_by_id():
    registry = mod.CredentialRegistry.from_path(REGISTRY)
    assert registry.connection(14435131).app == "notion"
    assert registry.connection(14438797).app == "wordpress"
    assert registry.connection(14428711).app == "facebook"
    assert registry.connection(14438016).app == "youtube"
    assert len(registry.connections_for_app("openai-gpt-3")) == 9


def test_rotated_social_secret_resolves_only_as_vault_reference():
    registry = mod.CredentialRegistry.from_path(REGISTRY)
    ref = registry.secret_reference("MAKE-SOCIAL-LEAD-INGEST-001")
    assert ref == "VAULT_REF:supabase://vault/cerebro_social_lead_ingest_current"
    assert "40TSP" not in REGISTRY.read_text(encoding="utf-8")
    assert "rUO6" not in REGISTRY.read_text(encoding="utf-8")

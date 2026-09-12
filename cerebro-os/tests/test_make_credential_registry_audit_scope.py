import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "identity" / "CREDENTIAL_REGISTRY_MAKE_2026-09-11.json"


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_inactive_test_audit_is_closed_and_secrets_remain_out_of_git():
    data = load_registry()
    assert data["policy"]["raw_secrets_in_git"] is False
    assert data["policy"]["reuse_existing_connections"] is True
    assert data["policy"]["do_not_reask_known_credentials"] is True
    assert data["audit_scope"]["inactive_test_scenarios"] == "AUDITED_117_OF_117_PRESERVED"


def test_registry_never_embeds_raw_secret_values():
    data = load_registry()
    for item in data["secrets"]:
        assert item["raw_value_stored_here"] is False

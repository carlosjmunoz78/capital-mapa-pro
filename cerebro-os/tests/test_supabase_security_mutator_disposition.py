from cerebro_os.runtime.supabase_security_mutator_disposition import (
    MUTATOR_DISPOSITION,
    PARITY_REQUIREMENTS,
    assess_mutator_disposition,
)


def test_mutator_surface_is_exactly_15_and_non_destructive():
    result = assess_mutator_disposition()
    assert result["mutator_count"] == 15
    assert result["all_unique"] is True
    assert result["automatic_prod_change_allowed"] is False
    assert result["automatic_grant_revoke_allowed"] is False
    assert result["automatic_retire_allowed"] is False


def test_all_mutators_require_wrap_review_until_parity_is_proven():
    assert set(MUTATOR_DISPOSITION.values()) == {"WRAP_REVIEW"}
    assert len(PARITY_REQUIREMENTS) == 8
    assert "rollback_path_proven" in PARITY_REQUIREMENTS
    assert "authz_scope_equivalence" in PARITY_REQUIREMENTS

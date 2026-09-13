from __future__ import annotations

EVIDENCE = {
    "captured_at": "2026-09-13",
    "source": "live_read_only_sql_expression_against_fenix_capital_prod",
    "primary_digits": "34600100200",
    "existing_digits": "600100200",
    "treated_as_same": False,
    "implication": "country_prefixed_and_local_phone_forms_are_distinct_under_current_normalization",
    "production_changed": False,
    "status": "CONTACTS_V2_FIXTURE_EXPECTATION_MUST_MATCH_CURRENT_BEHAVIOR",
}


def assess() -> dict:
    return dict(EVIDENCE)

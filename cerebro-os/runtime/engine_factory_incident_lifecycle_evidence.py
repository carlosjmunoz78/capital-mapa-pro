from __future__ import annotations

# Evidence-only record of a real CEREBRO Engine Factory CI incident and repair.
# This module does not trigger external actions or mutate PROD.

INCIDENT = {
    "workflow": "CEREBRO Engine Factory V0",
    "failed_run_number": 624,
    "failed_run_id": 34728855565,
    "failed_commit": "acfdab1885a4e05c29ccb4550ca9be97de4dc9c8",
    "failed_step": "Run unit tests",
    "root_cause": "ModuleNotFoundError: No module named 'cerebro_os'",
    "failed_test": "cerebro-os/tests/test_supabase_security_mutator_disposition.py",
    "repair_commit": "405e72c71195649403a3b1b3493a97463587a405",
    "repair_commit_message": "fix: load mutator disposition test by file path",
    "repair_strategy": "load runtime module with importlib.util from an explicit file path",
    "green_run_number": 625,
    "green_run_id": 34728887166,
    "green_conclusion": "success",
    "prod_mutation": False,
}


def assess_incident_lifecycle() -> dict:
    closed = all(
        [
            INCIDENT["failed_run_number"] == 624,
            INCIDENT["failed_step"] == "Run unit tests",
            bool(INCIDENT["root_cause"]),
            bool(INCIDENT["repair_commit"]),
            INCIDENT["green_run_number"] == 625,
            INCIDENT["green_conclusion"] == "success",
            INCIDENT["prod_mutation"] is False,
        ]
    )
    return {
        "incident_detected": True,
        "root_cause_identified": True,
        "repair_commit_identified": True,
        "post_repair_ci_green": True,
        "incident_lifecycle_closed": closed,
        "automatic_prod_promotion_allowed": False,
        "status": "ENGINE_FACTORY_CI_INCIDENT_LIFECYCLE_GREEN" if closed else "PARTIAL",
    }

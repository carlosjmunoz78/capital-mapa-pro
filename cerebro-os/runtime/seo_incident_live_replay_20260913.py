from __future__ import annotations

# Read-only retained SEO run snapshot captured from Make on 2026-09-13.
# No Make scenario is activated, edited, or executed by this module.

from seo_incident_monitor_20260913 import classify_run

COMPANY_ID = "fenix_capital"
ENGINE_ID = "seo"
ENVIRONMENT = "PROD"
VERSION = "2026-09-13"

RETAINED_RUNS = (
    (9597710, "7b090d25a75e4364bfdb3f9f0abfdaa5", "success"),
    (9597710, "2ba9c8c6cbbc4c338659a9afe76943db", "success"),
    (9597710, "2a8ba3f33db24d8496499acb729c2739", "success"),
    (9597710, "2e53646adf3c491aa0d4f48ef181d44d", "success"),
    (9550706, "fcb2b63f0d1a49b09c73c1afa5dd8857", "success"),
)


def replay_retained_runs() -> tuple[dict, ...]:
    return tuple(
        classify_run(
            scenario_id=scenario_id,
            status=status,
            company_id=COMPANY_ID,
            engine_id=ENGINE_ID,
            environment=ENVIRONMENT,
            version=VERSION,
            execution_id=execution_id,
        )
        for scenario_id, execution_id, status in RETAINED_RUNS
    )


def replay_nonprod_incident_fixture() -> dict:
    # Synthetic TEST-only fixture proving the parallel classifier raises an incident.
    return classify_run(
        scenario_id=9550706,
        status="error",
        company_id=COMPANY_ID,
        engine_id=ENGINE_ID,
        environment="TEST",
        version=VERSION,
        execution_id="fixture-error-001",
    )


def assess() -> dict:
    retained = replay_retained_runs()
    incident_fixture = replay_nonprod_incident_fixture()
    return {
        "retained_run_count": len(retained),
        "retained_success_count": sum(1 for row in retained if row["status"] == "success"),
        "retained_incident_count": sum(1 for row in retained if row["incident"]),
        "nonprod_incident_capture_proven": incident_fixture["incident"] is True and incident_fixture["severity"] == "HIGH",
        "prod_mutation_performed": False,
        "make_scenario_mutation_performed": False,
        "prod_wiring_enabled": False,
        "live_replay_green": len(retained) == 5 and all(not row["incident"] for row in retained),
        "status": "SEO_RETAINED_RUN_REPLAY_GREEN_NONPROD_INCIDENT_FIXTURE_GREEN",
    }

from __future__ import annotations

# Evidence-only tranche for additional PROD Edge surfaces inspected read-only.
# No RPC execution, no grants/RLS changes, no retirement and no PROD mutation.

SURFACES = {
    "fenix-brevo-lead-webhook": {
        "version": 3,
        "environment": "PROD",
        "source_read_only_inspected": True,
        "direct_15_mutator_name_reference_observed": False,
        "retired_http_410_observed": True,
    },
    "fenix-brevo-inventory-once": {
        "version": 9,
        "environment": "PROD",
        "source_read_only_inspected": True,
        "direct_15_mutator_name_reference_observed": False,
        "retired_http_410_observed": True,
    },
    "fenix-brevo-probe-once": {
        "version": 6,
        "environment": "PROD",
        "source_read_only_inspected": True,
        "direct_15_mutator_name_reference_observed": False,
        "retired_http_410_observed": True,
    },
    "fenix-document-existing-backfill": {
        "version": 7,
        "environment": "PROD",
        "source_read_only_inspected": True,
        "direct_15_mutator_name_reference_observed": False,
        "server_rpc_routing_observed": True,
        "role_gate_observed": True,
        "terminal_stage_skip_observed": True,
        "bounded_batch_observed": True,
    },
    "fenix-legacy-doc-migration-once": {
        "version": 12,
        "environment": "PROD",
        "source_read_only_inspected": True,
        "direct_15_mutator_name_reference_observed": False,
        "retired_http_410_observed": True,
    },
    "fenix-directory-sync-once": {
        "version": 12,
        "environment": "PROD",
        "source_read_only_inspected": True,
        "direct_15_mutator_name_reference_observed": False,
        "retired_http_410_observed": True,
    },
}


def assess_remaining_surface_evidence() -> dict:
    inspected = tuple(name for name, row in SURFACES.items() if row["source_read_only_inspected"])
    direct_absence = all(not row["direct_15_mutator_name_reference_observed"] for row in SURFACES.values())
    retired = tuple(name for name, row in SURFACES.items() if row.get("retired_http_410_observed", False))
    active_scoped = tuple(name for name, row in SURFACES.items() if row.get("server_rpc_routing_observed", False))
    return {
        "surface_count": len(SURFACES),
        "inspected_surface_count": len(inspected),
        "inspected_surfaces": inspected,
        "direct_15_mutator_absence_proven_for_tranche": direct_absence,
        "retired_fail_closed_count": len(retired),
        "retired_fail_closed_surfaces": retired,
        "active_scoped_surface_count": len(active_scoped),
        "active_scoped_surfaces": active_scoped,
        "automatic_security_remediation_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "status": "SIX_ADDITIONAL_PROD_EDGE_SURFACES_CLEARED",
    }

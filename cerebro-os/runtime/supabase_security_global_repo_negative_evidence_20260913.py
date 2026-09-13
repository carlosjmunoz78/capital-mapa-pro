from __future__ import annotations

# Read-only repository inventory evidence for SECURITY caller discovery.
# Negative code-search evidence is fail-closed: it does not prove global absence,
# safe retirement, or authorize any PROD privilege/RLS/grant change.

REPOSITORIES = (
    "carlosjmunoz78/fenix-capital-inmo-map",
    "carlosjmunoz78/capital-mapa-pro",
    "carlosjmunoz78/fenix-capital-cerebro-social",
    "carlosjmunoz78/fenix-core-guard",
    "carlosjmunoz78/buscador",
)

ADDITIONAL_REPOSITORY_PREFIX_SEARCH = {
    "carlosjmunoz78/fenix-capital-cerebro-social": 0,
    "carlosjmunoz78/fenix-core-guard": 0,
    "carlosjmunoz78/buscador": 0,
}

APP_KNOWN_DIRECT_CALLERS = 6
APP_REMAINING_MUTATORS_ZERO_INDEXED_MATCHES = 9
PROD_EDGE_SURFACES_READ_ONLY_INSPECTED = 33


def assess() -> dict:
    extra_zero = all(value == 0 for value in ADDITIONAL_REPOSITORY_PREFIX_SEARCH.values())
    return {
        "repository_count": len(REPOSITORIES),
        "repositories": REPOSITORIES,
        "additional_repository_count": len(ADDITIONAL_REPOSITORY_PREFIX_SEARCH),
        "additional_repositories_zero_fenix_prod_prefix_matches": extra_zero,
        "app_known_direct_caller_count": APP_KNOWN_DIRECT_CALLERS,
        "app_remaining_mutators_zero_indexed_match_count": APP_REMAINING_MUTATORS_ZERO_INDEXED_MATCHES,
        "prod_edge_surfaces_read_only_inspected": PROD_EDGE_SURFACES_READ_ONLY_INSPECTED,
        "global_absence_proven": False,
        "safe_retirement_proven": False,
        "caller_migration_complete": False,
        "prod_privilege_change_allowed": False,
        "automatic_prod_mutation_allowed": False,
        "status": "REPOSITORY_AND_EDGE_CALLER_INVENTORY_EXPANDED_FAIL_CLOSED",
    }

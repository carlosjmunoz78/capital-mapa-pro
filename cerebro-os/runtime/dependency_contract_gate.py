from __future__ import annotations

from dataclasses import dataclass

REQUIRED_SYSTEMS = (
    "app",
    "crm",
    "supabase",
    "notion",
    "wordpress",
    "seo",
)


@dataclass(frozen=True)
class DependencyContractEvidence:
    company_id: str
    engine_id: str
    environment: str
    version: str
    inventory_ref: str = ""
    dependency_map_ref: str = ""
    current_contract_ref: str = ""
    behavior_tests_ref: str = ""
    parallel_impl_ref: str = ""
    rollback_ref: str = ""
    covered_systems: tuple[str, ...] = ()


def assess_dependency_contract(evidence: DependencyContractEvidence) -> dict:
    if not all((evidence.company_id.strip(), evidence.engine_id.strip(), evidence.version.strip())):
        raise ValueError("company_id, engine_id and version required")

    refs = {
        "inventory": evidence.inventory_ref,
        "dependency_map": evidence.dependency_map_ref,
        "current_contract": evidence.current_contract_ref,
        "behavior_tests": evidence.behavior_tests_ref,
        "parallel_implementation": evidence.parallel_impl_ref,
        "rollback": evidence.rollback_ref,
    }
    missing_evidence = tuple(name for name, ref in refs.items() if not ref.strip())
    covered = set(evidence.covered_systems)
    missing_systems = tuple(system for system in REQUIRED_SYSTEMS if system not in covered)
    green = not missing_evidence and not missing_systems

    return {
        "company_id": evidence.company_id,
        "engine_id": evidence.engine_id,
        "environment": evidence.environment,
        "version": evidence.version,
        "required_systems": REQUIRED_SYSTEMS,
        "missing_evidence": missing_evidence,
        "missing_systems": missing_systems,
        "green": green,
        "prod_candidate_allowed": green,
        "old_systems_may_be_deleted": False,
        "migration_rule": "CONSERVAR_ENTENDER_ENVOLVER_PROBAR_MEJORAR_MIGRAR",
    }

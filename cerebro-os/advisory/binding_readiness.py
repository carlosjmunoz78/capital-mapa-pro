from __future__ import annotations

from dataclasses import dataclass

from .capabilities import CAPABILITY_REGISTRY

# Engine IDs with executable LAB primitives physically verified in the current
# repository modules. This is deliberately conservative: documentary coverage
# or canonical registration alone does not count as a runtime binding.
EXECUTABLE_LAB_ENGINES = frozenset({
    # cerebro-os/enterprise/engines.py
    "HR-001", "HR-002", "HR-003", "HR-004", "HR-005", "HR-006",
    "LEG-001", "TAX-001", "CMP-002", "DPO-001", "CONS-001",
    "INV-001", "COL-001", "TRE-001", "ACC-001",
    # cerebro-os/strategy/engines.py
    "STR-001", "FRC-001", "CAPA-001", "OPP-001", "INN-001", "EXP-001",
})


@dataclass(frozen=True)
class DomainBindingReadiness:
    domain: str
    required_engine_ids: tuple[str, ...]
    executable_engine_ids: tuple[str, ...]
    missing_engine_ids: tuple[str, ...]

    @property
    def status(self) -> str:
        if not self.required_engine_ids:
            return "UNBOUND"
        if not self.missing_engine_ids:
            return "FULLY_BINDABLE"
        if self.executable_engine_ids:
            return "PARTIALLY_BINDABLE"
        return "UNBOUND"


def binding_readiness(domain: str) -> DomainBindingReadiness:
    capability = CAPABILITY_REGISTRY[domain]
    executable = tuple(
        engine_id for engine_id in capability.engine_ids
        if engine_id in EXECUTABLE_LAB_ENGINES
    )
    missing = tuple(
        engine_id for engine_id in capability.engine_ids
        if engine_id not in EXECUTABLE_LAB_ENGINES
    )
    return DomainBindingReadiness(
        domain=domain,
        required_engine_ids=capability.engine_ids,
        executable_engine_ids=executable,
        missing_engine_ids=missing,
    )


def all_binding_readiness() -> tuple[DomainBindingReadiness, ...]:
    return tuple(binding_readiness(domain) for domain in CAPABILITY_REGISTRY)


def capability_binding_summary() -> dict[str, int]:
    rows = all_binding_readiness()
    return {
        "domains": len(rows),
        "fully_bindable": sum(row.status == "FULLY_BINDABLE" for row in rows),
        "partially_bindable": sum(row.status == "PARTIALLY_BINDABLE" for row in rows),
        "unbound": sum(row.status == "UNBOUND" for row in rows),
    }

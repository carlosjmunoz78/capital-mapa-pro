"""TECH-SCOUT isolated gateway capability map; default OFF and LAB only."""
from __future__ import annotations
from dataclasses import dataclass

CAPABILITIES = ("TECHSCOUT.READ", "TECHSCOUT.PROPOSE", "TECHSCOUT.PROBE")

@dataclass(frozen=True)
class TechScoutGate:
    company_id: str = "fenix-capital"
    engine_id: str = "TECH-SCOUT"
    environment: str = "LAB"
    version: str = "0.1.0"
    enabled: bool = False
    caller_authenticated: bool = False
    policy_approved: bool = False
    audit_ready: bool = False
    rollback_ready: bool = False
    money_limit_eur: int = 0

    def eligible(self) -> bool:
        return (bool(self.company_id and self.company_id.strip())
                and self.engine_id == "TECH-SCOUT"
                and self.version == "0.1.0"
                and self.environment == "LAB"
                and self.enabled and self.caller_authenticated
                and self.policy_approved and self.audit_ready
                and self.rollback_ready and self.money_limit_eur == 0)

def register_techscout(registry, gate: TechScoutGate):
    """Register LAB-only connector routes once a trusted Gateway E2E grant is proven.

    This pure router is not an authenticator and performs no data or network access.
    """
    if not gate.eligible():
        return {"status":"BLOCKED","reason":"GATEWAY_E2E_REQUIRED"}
    from connectors.registry import ConnectorCapability
    for capability in CAPABILITIES:
        registry.register(ConnectorCapability(
            connector_id="TECH-SCOUT-LAB-" + capability.rsplit(".",1)[1],
            capability=capability,
            route_type="OFFICIAL_API",
            company_id=gate.company_id,
            environment=gate.environment,
            version=gate.version,
        ))
    return {"status":"REGISTERED_LAB","capabilities":CAPABILITIES}

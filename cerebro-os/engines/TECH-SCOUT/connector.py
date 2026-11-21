"""TECH-SCOUT connector wiring. Default-disabled and LAB-only; no network access."""
from __future__ import annotations
from dataclasses import dataclass

CAPABILITIES = ("TECHSCOUT.READ", "TECHSCOUT.PROPOSE")

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
        return (self.enabled and self.environment == "LAB" and
                self.caller_authenticated and self.policy_approved and
                self.audit_ready and self.rollback_ready and
                self.money_limit_eur == 0)

def register_techscout(registry, gate: TechScoutGate):
    """Register routes only if all external integration gates already verified green.

    The caller imports the existing registry as a package from cerebro-os.
    This adapter deliberately does not perform any HTTP or credential operations.
    """
    if not gate.eligible() or not gate.company_id or gate.engine_id != "TECH-SCOUT":
        return {"status": "BLOCKED", "reason": "GATEWAY_E2E_REQUIRED"}
    from connectors.registry import ConnectorCapability
    for capability in CAPABILITIES:
        registry.register(ConnectorCapability(
            connector_id="TECH-SCOUT-LAB-" + capability.rsplit(".", 1)[1],
            capability=capability,
            route_type="OFFICIAL_API",
            company_id=gate.company_id,
            environment="LAB",
            version=gate.version,
        ))
    return {"status":"REGISTERED_LAB", "capabilities":CAPABILITIES}

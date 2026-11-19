"""Additive LAB-only registration for CEREBRO's existing Gateway.

No global registration, no network, no runtime deployment and no PROD changes.
A ROUTED outcome is never evidence that a specialist consumed knowledge.
"""
from __future__ import annotations

CONNECTOR_ID = "KNOWLEDGE-GOOGLE-SHEETS-LAB-001"
CAPABILITY = "KNOWLEDGE.READ"

# Immutable sourced inventory, not tenant aliases or grants to other engines.
LAB_ENGINE_SCOPES = {
    "fenix-capital": frozenset((
        "SOC-FB-FINANCIAL-REAL-ESTATE-V1",
        "SOC-001/SOCBOOT-001",
        "SOC-LI-FINANCIAL-REAL-ESTATE-V1",
    )),
    "fenix": frozenset(("SEO-001",)),
}


def register_knowledge_lab_capabilities(*, registry, connector_type, enabled: bool = False) -> tuple[str, ...]:
    """Register exact LAB capabilities only after runtime IAM is physically verified.

    This function does NOT activate merely because a connector object exists.
    The default is fail-closed. It adds nothing to the supplied registry until
    enabled is explicitly True at the trusted runtime composition root.
    """
    if enabled is not True:
        return ()
    for company in LAB_ENGINE_SCOPES:
        registry.register(connector_type(
            connector_id=CONNECTOR_ID,
            capability=CAPABILITY,
            route_type="OFFICIAL_API",
            company_id=company,
            environment="LAB",
            enabled=True,
        ))
    return tuple(LAB_ENGINE_SCOPES)


def knowledge_lab_policy(base_policy):
    """Conjoin the existing Gateway policy with exact company-engine LAB scopes.

    Callers must also check full agent/subagent/version grants and the separate
    Node adapter's verified Google reader. This is routing policy only.
    """
    if not callable(base_policy):
        raise TypeError("BASE_POLICY_REQUIRED")

    def check(request):
        allowed, reason = base_policy(request)
        if not allowed:
            return False, reason
        if request.capability != CAPABILITY:
            return allowed, reason
        if request.environment != "LAB":
            return False, "POLICY_CONFLICT"
        if request.engine_id not in LAB_ENGINE_SCOPES.get(request.company_id, frozenset()):
            return False, "POLICY_CONFLICT"
        return True, None

    return check
"""Offline composition of existing tenant and governance policy for catalog reads.
Not an authentication adapter. The selected company must originate from a
separately authenticated and authorized runtime. No identity is granted here.
The original signed catalog package is unchanged.
"""
from gateway.service import GatewayRequest
from gateway import catalog_read as c
from governance.policy import PolicyRequest, evaluate
from governance.tenant import assert_tenant_access
import math

def evaluate_catalog_scope(request, *, selected_company_id, facts):
    """Only policy evaluation; never a live permission or release decision."""
    def deny(reason):
        return {"decision":"DENY","reasons":[reason],"runtime_identity_verified":False}
    if type(request) is not GatewayRequest or (
        request.company_id,request.engine_id,request.capability,request.environment,request.version
    )!=(c.COMPANY,c.ENGINE,c.CAPABILITY,c.ENV,c.VERSION):
        return deny("CATALOG_SCOPE_DENIED")
    try:
        assert_tenant_access(selected_company_id,request.company_id,global_only=False)
    except PermissionError:
        return deny("CROSS_COMPANY_DENIED")
    if type(facts) is not PolicyRequest:
        return deny("POLICY_CONTEXT_REQUIRED")
    if (facts.company_id,facts.target_company_id,facts.environment,facts.action)!=(
        selected_company_id,request.company_id,c.ENV,c.CAPABILITY):
        return deny("POLICY_SCOPE_DENIED")
    if any(type(getattr(facts,k)) is not bool for k in ("irreversible","touches_prod",
        "legal_required","signature_required","customer_human_request")):
        return deny("POLICY_CONTEXT_INVALID")
    if facts.irreversible or facts.touches_prod:
        return deny("READ_ONLY_CONTRACT_VIOLATION")
    if type(facts.risk) is not str or facts.risk not in {"LOW","MEDIUM","HIGH"}:
        return deny("POLICY_CONTEXT_INVALID")
    for x in (facts.cost_eur,facts.money_limit_eur,facts.confidence):
        if type(x) not in (int,float) or not math.isfinite(x) or x<0:
            return deny("POLICY_CONTEXT_INVALID")
    if facts.confidence>1 or facts.money_limit_eur!=0:
        return deny("POLICY_CONTEXT_INVALID")
    return {**evaluate(facts),"runtime_identity_verified":False}

def offline_policy_callback(*, selected_company_id, facts):
    """For local acceptance only, never use as sole runtime authentication."""
    def check(request):
        r=evaluate_catalog_scope(request,selected_company_id=selected_company_id,facts=facts)
        return r["decision"]=="ALLOW", (r["reasons"] or [None])[0]
    return check

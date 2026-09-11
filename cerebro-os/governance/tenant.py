from __future__ import annotations


def assert_tenant_access(actor_company_id: str | None, resource_company_id: str | None, global_only: bool = False) -> None:
    if global_only:
        return
    if not actor_company_id or not resource_company_id:
        raise PermissionError("company_id required")
    if actor_company_id != resource_company_id:
        raise PermissionError("cross-company access denied")

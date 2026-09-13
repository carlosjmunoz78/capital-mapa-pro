from __future__ import annotations

EVIDENCE = {
    "project_ref": "hnqlnvakzaywtafeiybt",
    "schema": "cerebro_security_lab_20260913",
    "table": "replay_probe",
    "rls_enabled": True,
    "force_rls": False,
    "policy_count": 0,
    "row_count": 0,
    "relacl_is_null": True,
    "prod_touched": False,
    "app_touched": False,
    "crm_touched": False,
}


def assess() -> dict:
    fail_closed = EVIDENCE["rls_enabled"] and EVIDENCE["policy_count"] == 0 and EVIDENCE["row_count"] == 0
    return {
        **EVIDENCE,
        "fail_closed_lab_green": fail_closed,
        "real_business_replay_proven": False,
        "prod_parity_green": False,
        "status": "LAB_BOUNDARY_PROVEN_BUSINESS_REPLAY_PENDING" if fail_closed else "LAB_BOUNDARY_NOT_PROVEN",
    }

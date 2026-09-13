from __future__ import annotations

# Evidence snapshot only. No external mutation is performed here.
YOUTUBE_HEALTH_EVIDENCE = {
    "scenario_id": 9537666,
    "scenario_name": "FENIX · HEALTH · YouTube · Canal, vídeos y permisos · V1",
    "connection_id": 14591497,
    "connection_status": "ok",
    "execution_id": "8748fa64f694410e845bd220ab223733",
    "execution_status": "success",
    "operations": 3,
    "credits": 3,
    "data_transfer_bytes": 3944,
    "scenario_returned_inactive": True,
    "retained_metric_execution_proven": True,
    "publishing_or_video_mutation_performed": False,
    "app_crm_prod_modified": False,
}


def assess_youtube_retained_health() -> dict:
    row = dict(YOUTUBE_HEALTH_EVIDENCE)
    row["green"] = bool(
        row["connection_status"] == "ok"
        and row["execution_status"] == "success"
        and row["retained_metric_execution_proven"]
        and row["scenario_returned_inactive"]
        and not row["publishing_or_video_mutation_performed"]
        and not row["app_crm_prod_modified"]
    )
    return row

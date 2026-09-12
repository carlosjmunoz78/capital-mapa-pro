from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class GscCaptureContract:
    company_id: str
    engine_id: str
    environment: str
    version: str
    scenario_id: int
    site_url: str
    window_days: int
    dimensions: tuple[str, ...]
    mutates_notion_metrics_only: bool
    connection_ok: bool

    def validate(self) -> None:
        required = (self.company_id, self.engine_id, self.environment, self.version, self.site_url)
        if any(not str(v).strip() for v in required):
            raise ValueError("GSC capture contract missing required scope")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.window_days <= 0:
            raise ValueError("window_days must be positive")
        if not self.dimensions:
            raise ValueError("at least one GSC dimension is required")


def assess_gsc_edge(contract: GscCaptureContract) -> dict:
    """Classify the live Make GSC edge without replacing or executing it.

    The active Make scenario is preserved. CEREBRO may wrap/interpret the data,
    but this runtime function never calls GSC and never mutates Notion.
    """
    contract.validate()
    blocker = None if contract.connection_ok else "CONNECTION_NOT_OK"
    return {
        "company_id": contract.company_id,
        "engine_id": contract.engine_id,
        "environment": contract.environment,
        "version": contract.version,
        "scenario_id": contract.scenario_id,
        "site_url": contract.site_url,
        "window_days": contract.window_days,
        "dimensions": contract.dimensions,
        "edge_preserved": True,
        "connection_ok": contract.connection_ok,
        "metric_write_scope_only": contract.mutates_notion_metrics_only,
        "runtime_external_action_allowed": False,
        "runtime_notion_mutation_allowed": False,
        "migration_required": False,
        "status": "LIVE_EDGE_PRESERVE_GREEN" if blocker is None else "BLOCKED_LIVE_EDGE",
        "blockers": () if blocker is None else (blocker,),
    }


PROD_GSC_SCENARIOS = {
    9597710: {
        "name": "GSC_30D_TO_NOTION_INVENTORY_V2",
        "dimensions": ("PAGE",),
        "mutates_notion_metrics_only": True,
    },
    9550706: {
        "name": "GSC_WEEKLY_WATCH_V1",
        "dimensions": ("QUERY", "PAGE", "DEVICE", "COUNTRY"),
        "mutates_notion_metrics_only": False,
    },
}


def inventory() -> dict[int, dict]:
    return {k: dict(v) for k, v in PROD_GSC_SCENARIOS.items()}

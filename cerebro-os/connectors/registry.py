from __future__ import annotations

from dataclasses import dataclass

PRIORITY = {"OFFICIAL_API": 0, "MCP": 1, "WEBHOOK": 2, "SCRIPT": 3, "BROWSER": 4}
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


@dataclass(frozen=True)
class ConnectorCapability:
    connector_id: str
    capability: str
    route_type: str
    company_id: str | None = None
    enabled: bool = True
    environment: str | None = None

    def validate(self) -> None:
        if self.route_type not in PRIORITY:
            raise ValueError("unsupported route_type")
        if not self.connector_id or not self.capability:
            raise ValueError("connector_id and capability are required")
        if self.environment is not None and self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")


class ConnectorRegistry:
    def __init__(self) -> None:
        self._items: list[ConnectorCapability] = []

    def register(self, item: ConnectorCapability) -> None:
        item.validate()
        self._items.append(item)

    def route(self, capability: str, company_id: str, environment: str = "LAB") -> ConnectorCapability | None:
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        candidates = [
            item for item in self._items
            if item.enabled
            and item.capability == capability
            and item.company_id in {None, company_id}
            and item.environment in {None, environment}
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: PRIORITY[item.route_type])[0]

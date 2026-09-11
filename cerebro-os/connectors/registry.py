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
    version: str | None = None

    def validate(self) -> None:
        if self.route_type not in PRIORITY:
            raise ValueError("unsupported route_type")
        if not self.connector_id or not self.capability:
            raise ValueError("connector_id and capability are required")
        if self.environment is not None and self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if self.version is not None and not self.version.strip():
            raise ValueError("version cannot be blank")


class ConnectorRegistry:
    def __init__(self) -> None:
        self._items: list[ConnectorCapability] = []

    def register(self, item: ConnectorCapability) -> None:
        item.validate()
        self._items.append(item)

    def route(self, capability: str, company_id: str, environment: str = "LAB", version: str = "1.0.0") -> ConnectorCapability | None:
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        if not company_id.strip() or not version.strip():
            raise ValueError("company_id and version are required")
        candidates = [
            item for item in self._items
            if item.enabled
            and item.capability == capability
            and item.company_id in {None, company_id}
            and item.environment in {None, environment}
            and item.version in {None, version}
        ]
        if not candidates:
            return None
        return sorted(
            candidates,
            key=lambda item: (
                PRIORITY[item.route_type],
                0 if item.company_id == company_id else 1,
                0 if item.environment == environment else 1,
                0 if item.version == version else 1,
                item.connector_id,
            ),
        )[0]

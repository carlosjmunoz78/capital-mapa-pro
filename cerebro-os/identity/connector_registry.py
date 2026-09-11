from dataclasses import dataclass, field
from typing import List

PRIORITY = {"OFFICIAL_API":0,"MCP":1,"WEBHOOK":2,"SCRIPT":3,"BROWSER":4}
VALID_ENVIRONMENTS = {"LAB","PREPROD","PROD"}

@dataclass(frozen=True)
class ConnectorCapability:
    connector_id: str
    company_id: str
    capability: str
    connector_type: str
    environment: str
    active: bool = True
    version: str = "1.0.0"

    def validate(self):
        if self.connector_type not in PRIORITY: raise ValueError("unsupported connector type")
        if self.environment not in VALID_ENVIRONMENTS: raise ValueError("invalid environment")
        if not all([self.connector_id,self.company_id,self.capability,self.version]): raise ValueError("missing connector field")
        return True

@dataclass
class ConnectorRegistry:
    connectors: List[ConnectorCapability] = field(default_factory=list)

    def register(self, item):
        item.validate()
        self.connectors.append(item)

    def route(self, company_id, capability, environment, version="1.0.0"):
        if environment not in VALID_ENVIRONMENTS or not version:
            raise ValueError("invalid connector route scope")
        matches=[c for c in self.connectors if c.active and c.company_id==company_id and c.capability==capability and c.environment==environment and c.version==version]
        if not matches: return None
        return sorted(matches,key=lambda c: PRIORITY[c.connector_type])[0]

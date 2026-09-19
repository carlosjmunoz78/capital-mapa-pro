from __future__ import annotations

from dataclasses import dataclass
from connector_registry import ConnectorRegistry

BUILDABLE_TYPES=("OWN_API","WEBHOOK","SCRIPT","CLI","MCP","BUILT_CONNECTOR")

@dataclass(frozen=True)
class ConnectorGapRequest:
    company_id:str
    capability:str
    environment:str
    version:str="1.0.0"
    official_api_known:bool=False
    existing_connector_known:bool=False
    mcp_known:bool=False
    browser_only_possible:bool=False
    estimated_cost_eur:float=0.0
    legal_or_terms_risk:bool=False

    def validate(self)->None:
        if not all(str(x).strip() for x in (self.company_id,self.capability,self.environment,self.version)):
            raise ValueError("connector gap scope required")
        if self.environment not in {"LAB","PREPROD","PROD"}:
            raise ValueError("invalid environment")
        if self.estimated_cost_eur<0:
            raise ValueError("estimated cost must be non-negative")

def plan_connector_gap(req:ConnectorGapRequest,registry:ConnectorRegistry)->dict:
    req.validate()
    existing=registry.route(req.company_id,req.capability,req.environment,req.version)
    if existing is not None:
        return {
          "status":"GREEN","decision":"REUSE_EXISTING_CONNECTOR",
          "connector_id":existing.connector_id,"connector_type":existing.connector_type,
          "factory_request":None,"human_reason":None,"cost_eur":0.0,
        }

    if req.official_api_known:
        return {
          "status":"DEFINED","decision":"INTEGRATE_OFFICIAL_API",
          "connector_id":None,"connector_type":"OFFICIAL_API","factory_request":{
            "artifact_type":"CONNECTOR","preferred_type":"OFFICIAL_API","capability":req.capability,
            "company_id":req.company_id,"environment":req.environment,"version":req.version,
            "requirements":["manifest","permissions","contracts","tests","observability","rate_limits","cost","rollback","rebuild"],
          },"human_reason":None,"cost_eur":0.0,
        }

    if req.existing_connector_known:
        return {
          "status":"DEFINED","decision":"WRAP_EXISTING_CONNECTOR",
          "connector_id":None,"connector_type":"EXISTING_CONNECTOR","factory_request":None,
          "human_reason":None,"cost_eur":0.0,
        }

    if req.mcp_known:
        return {
          "status":"DEFINED","decision":"INTEGRATE_EXISTING_MCP",
          "connector_id":None,"connector_type":"MCP","factory_request":None,
          "human_reason":None,"cost_eur":0.0,
        }

    if req.legal_or_terms_risk:
        return {
          "status":"HUMAN_REQUIRED","decision":"CONNECTOR_GAP_REQUIRES_POLICY_REVIEW",
          "connector_id":None,"connector_type":None,"factory_request":None,
          "human_reason":"POLICY_CONFLICT","cost_eur":0.0,
        }

    if req.estimated_cost_eur>0:
        return {
          "status":"HUMAN_REQUIRED","decision":"PAID_CONNECTOR_NOT_AUTO_APPROVED",
          "connector_id":None,"connector_type":None,"factory_request":None,
          "human_reason":"MONEY_LIMIT","cost_eur":req.estimated_cost_eur,
        }

    if req.browser_only_possible:
        return {
          "status":"DEFINED","decision":"USE_BROWSER_FALLBACK_POLICY",
          "connector_id":None,"connector_type":"COMPUTER_USE","factory_request":None,
          "human_reason":None,"cost_eur":0.0,
        }

    return {
      "status":"DEFINED","decision":"FACTORY_BUILD_CONNECTOR_CANDIDATE",
      "connector_id":None,"connector_type":"BUILT_CONNECTOR",
      "factory_request":{
        "artifact_type":"CONNECTOR","preferred_type":"SCRIPT_OR_API_ADAPTER","capability":req.capability,
        "company_id":req.company_id,"environment":req.environment,"version":req.version,
        "requirements":["manifest","permissions","contracts","secret_refs_only","tests","evaluation","observability","rate_limits","cost","backup","rollback","rebuild","documentation"],
        "external_mutation_allowed":False,"prod_activation_allowed":False,
      },
      "human_reason":None,"cost_eur":0.0,
    }

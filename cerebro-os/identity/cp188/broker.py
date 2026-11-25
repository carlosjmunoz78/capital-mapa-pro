"""CP188: provider-managed credentials, exact operation and scope; no raw secret returned.
LAB/PREPROD providers unchanged; exact PROD catalog scope is opt-in and fail-closed.
Runtime-configured adapter, not a public credential endpoint.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import os
import subprocess

@dataclass(frozen=True)
class Scope:
    company_id: str
    engine_id: str
    account_id: str
    environment: str
    version: str
    operation: str

FORGE = Scope("fenix", "FORGE", "forge-reader", "PREPROD", "1.0.0", "FORGE.SERVICE.READ")
PROJECT = "cerebro-forge"
REGION = "europe-southwest1"
SERVICE = "cerebro-advisory-preprod"
ACCOUNT = "cerebro-forge-broker-reader@cerebro-forge.iam.gserviceaccount.com"
AUDIENCE = "//iam.googleapis.com/projects/15609183753/locations/global/workloadIdentityPools/github-cerebro-forge/providers/github-provider"
IMPERSONATION = "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/" + ACCOUNT + ":generateAccessToken"
EXPECTED_REF = "refs/heads/cerebro-engine-factory-v0"
EXPECTED_REPO = "carlosjmunoz78/capital-mapa-pro"

# Logical account alias only: not a provisioned service identity or grant.
FACT_CATALOG_PROD = Scope("fenix", "FACT-001", "fact-catalog-reader",
                          "PROD", "1.2.0", "FACT.CATALOG.READ")

class ScopedCredentialBroker:
    def __init__(self, *, providers, prod_authorizer=None):
        self._providers = dict(providers)
        # Trusted runtime dependency, never supplied by the request. Must
        # independently verify live identity, scope and release authorization.
        # No default, no fallback to the LAB/PREPROD provider.
        self._prod_authorizer = prod_authorizer

    def execute(self, scope):
        if type(scope) is not Scope or scope.environment not in ("LAB", "PREPROD", "PROD"):
            raise PermissionError("CREDENTIAL_ENVIRONMENT_DENIED")
        if scope.environment == "PROD":
            if scope != FACT_CATALOG_PROD:
                raise PermissionError("CREDENTIAL_SCOPE_DENIED")
            if not callable(self._prod_authorizer):
                raise PermissionError("PROD_AUTHORITY_REQUIRED")
            try:
                granted = self._prod_authorizer(scope)
            except Exception:
                raise PermissionError("PROD_AUTHORITY_DENIED") from None
            if granted is not True:
                raise PermissionError("PROD_AUTHORITY_DENIED")
        adapter = self._providers.get(scope)
        if adapter is None:
            raise PermissionError("CREDENTIAL_SCOPE_DENIED")
        # Return only adapter-defined non-secret, operation-specific receipt.
        return adapter()

class ForgeFederatedRead:
    def __init__(self, *, env=None, run=None):
        self._env = os.environ if env is None else env
        self._run = subprocess.run if run is None else run

    def _gcloud(self, args):
        p = self._run(["gcloud", "--quiet", *args], capture_output=True, text=True, timeout=40,
                      check=False)
        if p.returncode != 0:
            raise PermissionError("PROVIDER_OPERATION_DENIED")
        try:
            return json.loads(p.stdout)
        except (ValueError, TypeError):
            raise PermissionError("PROVIDER_RESPONSE_DENIED") from None

    def __call__(self):
        e = self._env
        if e.get("GITHUB_ACTIONS") != "true" or e.get("GITHUB_REPOSITORY") != EXPECTED_REPO or e.get("GITHUB_REF") != EXPECTED_REF:
            raise PermissionError("FEDERATED_RUNTIME_DENIED")
        path = e.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not path or e.get("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE") != path:
            raise PermissionError("FEDERATED_CREDENTIAL_REFERENCE_REQUIRED")
        try:
            with Path(path).open(encoding="utf-8") as f:
                c = json.load(f)
        except (OSError, ValueError):
            raise PermissionError("FEDERATED_REFERENCE_UNAVAILABLE") from None
        if (c.get("type") != "external_account" or c.get("audience") != AUDIENCE
                or c.get("service_account_impersonation_url") != IMPERSONATION
                or c.get("token_url") != "https://sts.googleapis.com/v1/token"
                or "private_key" in c):
            raise PermissionError("FEDERATED_REFERENCE_DENIED")
        accounts = self._gcloud(["auth", "list", "--filter=status:ACTIVE", "--format=json"])
        if not isinstance(accounts, list) or [x.get("account") for x in accounts] != [ACCOUNT]:
            raise PermissionError("FEDERATED_ACCOUNT_DENIED")
        service = self._gcloud(["run", "services", "describe", SERVICE, "--project="+PROJECT,
                               "--region="+REGION, "--format=json"])
        meta, status = service.get("metadata", {}), service.get("status", {})
        annotations = meta.get("annotations", {})
        traffic = [t for t in status.get("traffic", []) if t.get("percent", 0)>0]
        if (meta.get("name") != SERVICE or annotations.get("run.googleapis.com/ingress") != "internal"
                or len(traffic)!=1 or traffic[0].get("percent")!=100
                or not traffic[0].get("revisionName")):
            raise PermissionError("PROVIDER_TARGET_DENIED")
        return {"status":"CP188_FEDERATED_READ_VERIFIED", "company_id":"fenix",
                "environment":"PREPROD", "engine_id":"FORGE", "operation":"FORGE.SERVICE.READ",
                "provider":"GOOGLE_WIF", "identity_verified":True, "credential_value_exposed":False,
                "serving_revision":traffic[0]["revisionName"], "external_mutation":False,
                "promotion_allowed":False}

if __name__ == "__main__":
    print(json.dumps(ScopedCredentialBroker(providers={FORGE:ForgeFederatedRead()}).execute(FORGE),sort_keys=True))

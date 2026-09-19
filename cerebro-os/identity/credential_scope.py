from __future__ import annotations

from dataclasses import dataclass

VALID_ENVIRONMENTS={"LAB","PREPROD","PROD"}

@dataclass(frozen=True)
class ScopedCredentialRef:
    credential_ref_id:str
    account_id:str
    identity_id:str
    company_id:str
    vault_provider:str
    secret_ref:str
    environment:str="LAB"
    version:str="1.0.0"
    scopes:tuple[str,...]=()
    expires_at:str|None=None
    rotation_policy:str="PROVIDER_MANAGED"
    recovery_method:str="PROVIDER_STANDARD"

    def validate(self)->None:
        required=(self.credential_ref_id,self.account_id,self.identity_id,self.company_id,self.vault_provider,self.secret_ref,self.version,self.rotation_policy,self.recovery_method)
        if not all(str(x).strip() for x in required):
            raise ValueError("credential reference scope fields required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid credential environment")
        forbidden=("password=","token=","secret=","apikey=","api_key=")
        if any(x in self.secret_ref.lower() for x in forbidden):
            raise ValueError("embedded secret value forbidden")
        if self.vault_provider not in {"ENV","GITHUB_SECRETS","SUPABASE_SECRETS","VAULT_REF","PROVIDER_MANAGED"}:
            raise ValueError("unsupported vault provider")

def authorize_credential_ref(*,credential:ScopedCredentialRef,company_id:str,identity_id:str,account_id:str,environment:str,version:str)->dict:
    credential.validate()
    requested=(company_id,identity_id,account_id,environment,version)
    actual=(credential.company_id,credential.identity_id,credential.account_id,credential.environment,credential.version)
    if requested!=actual:
        raise PermissionError("credential scope mismatch")
    return {
      "credential_ref_id":credential.credential_ref_id,
      "account_id":credential.account_id,
      "identity_id":credential.identity_id,
      "company_id":credential.company_id,
      "vault_provider":credential.vault_provider,
      "secret_ref":credential.secret_ref,
      "environment":credential.environment,
      "version":credential.version,
      "scopes":credential.scopes,
      "secret_value_exposed":False,
      "authorized":True,
    }

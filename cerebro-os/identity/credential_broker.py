from dataclasses import dataclass

@dataclass(frozen=True)
class CredentialHandle:
    company_id: str
    account_id: str
    provider: str
    secret_ref: str
    environment: str

    def validate(self):
        if self.environment not in {"LAB","PREPROD","PROD"}: raise ValueError("invalid environment")
        if not all([self.company_id,self.account_id,self.provider,self.secret_ref]): raise ValueError("missing credential metadata")
        forbidden = ("token=", "password=", "secret=", "apikey=")
        if any(x in self.secret_ref.lower() for x in forbidden): raise ValueError("embedded secret value forbidden")
        return True

class CredentialBroker:
    def resolve(self, handle: CredentialHandle):
        handle.validate()
        return {"secret_ref": handle.secret_ref, "provider": handle.provider, "resolved": False}

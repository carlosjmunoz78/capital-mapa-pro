from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

VALID_ENVIRONMENTS={"LAB","PREPROD","PROD"}
VALID_LOGIN_METHODS={"EMAIL_PASSWORD","GOOGLE","MICROSOFT","APPLE","SOCIAL","PASSKEY","OAUTH","SSO","SESSION","API_KEY","TOKEN","OTHER"}

@dataclass(frozen=True)
class IdentityRecord:
    identity_id:str
    owner_type:str
    owner_id:str
    company_id:str
    display_name:str
    policy_set:str
    environment:str="LAB"
    version:str="1.0.0"
    status:str="ACTIVE"

    def validate(self)->None:
        if not all(str(x).strip() for x in (self.identity_id,self.owner_type,self.owner_id,self.company_id,self.display_name,self.policy_set,self.version)):
            raise ValueError("identity scope fields required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid identity environment")

@dataclass(frozen=True)
class AccountRecord:
    account_id:str
    identity_id:str
    company_id:str
    provider:str
    handle_or_email:str
    login_method:str
    purpose:str
    environment:str="LAB"
    version:str="1.0.0"
    status:str="ACTIVE"
    verified_at:str|None=None

    def validate(self)->None:
        if not all(str(x).strip() for x in (self.account_id,self.identity_id,self.company_id,self.provider,self.handle_or_email,self.login_method,self.purpose,self.version)):
            raise ValueError("account scope fields required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid account environment")
        if self.login_method not in VALID_LOGIN_METHODS:
            raise ValueError("unsupported login method")

@dataclass
class IdentityAccountRegistry:
    identities:List[IdentityRecord]=field(default_factory=list)
    accounts:List[AccountRecord]=field(default_factory=list)

    def register_identity(self,item:IdentityRecord)->None:
        item.validate()
        if any(x.identity_id==item.identity_id for x in self.identities):
            raise ValueError("duplicate identity_id")
        self.identities.append(item)

    def register_account(self,item:AccountRecord)->None:
        item.validate()
        identity=next((x for x in self.identities if x.identity_id==item.identity_id),None)
        if identity is None:
            raise ValueError("identity not registered")
        if identity.company_id!=item.company_id:
            raise ValueError("cross-company account identity denied")
        if identity.environment!=item.environment or identity.version!=item.version:
            raise ValueError("account identity scope mismatch")
        if any(x.account_id==item.account_id for x in self.accounts):
            raise ValueError("duplicate account_id")
        self.accounts.append(item)

    def accounts_for(self,company_id:str,environment:str,version:str="1.0.0")->tuple[AccountRecord,...]:
        if not company_id.strip() or environment not in VALID_ENVIRONMENTS or not version.strip():
            raise ValueError("valid company/environment/version required")
        return tuple(x for x in self.accounts if x.company_id==company_id and x.environment==environment and x.version==version)

    def account(self,company_id:str,account_id:str,environment:str,version:str="1.0.0")->AccountRecord:
        matches=[x for x in self.accounts if x.company_id==company_id and x.account_id==account_id and x.environment==environment and x.version==version]
        if not matches:
            raise KeyError(account_id)
        return matches[0]

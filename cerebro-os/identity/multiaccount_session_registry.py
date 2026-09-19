from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

VALID_ENVIRONMENTS={"LAB","PREPROD","PROD"}

@dataclass(frozen=True)
class SessionBinding:
    session_id:str
    company_id:str
    identity_id:str
    account_id:str
    provider:str
    profile_id:str
    device_id:str
    browser_family:str
    environment:str="LAB"
    version:str="1.0.0"
    authenticated:bool=False
    evidence_ref:str=""
    status:str="ACTIVE"

    def validate(self)->None:
        required=(self.session_id,self.company_id,self.identity_id,self.account_id,self.provider,self.profile_id,self.device_id,self.browser_family,self.environment,self.version)
        if not all(str(x).strip() for x in required):
            raise ValueError("session binding scope required")
        if self.environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid session environment")

@dataclass
class MultiAccountSessionRegistry:
    sessions:List[SessionBinding]=field(default_factory=list)

    def register(self,item:SessionBinding)->None:
        item.validate()
        if any(x.session_id==item.session_id for x in self.sessions):
            raise ValueError("duplicate session_id")
        self.sessions.append(item)

    def by_account(self,company_id:str,account_id:str,environment:str,version:str="1.0.0")->tuple[SessionBinding,...]:
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        return tuple(
            x for x in self.sessions
            if x.company_id==company_id and x.account_id==account_id and x.environment==environment and x.version==version
        )

    def resolve_authenticated(self,company_id:str,account_id:str,environment:str,version:str="1.0.0")->SessionBinding|None:
        rows=[x for x in self.by_account(company_id,account_id,environment,version) if x.authenticated and x.status=="ACTIVE"]
        if not rows:
            return None
        return sorted(rows,key=lambda x:(x.profile_id,x.device_id,x.session_id))[0]

    def assert_scope(self,session:SessionBinding,*,company_id:str,identity_id:str,account_id:str,environment:str,version:str)->None:
        actual=(session.company_id,session.identity_id,session.account_id,session.environment,session.version)
        expected=(company_id,identity_id,account_id,environment,version)
        if actual!=expected:
            raise PermissionError("session scope mismatch")

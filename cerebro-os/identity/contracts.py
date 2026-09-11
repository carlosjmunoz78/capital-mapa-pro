from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class Identity:
    identity_id: str
    owner_type: str
    owner_id: str
    company_id: str
    display_name: str
    status: str = "ACTIVE"

@dataclass(frozen=True)
class Account:
    account_id: str
    identity_id: str
    provider: str
    handle: str
    login_method: str
    purpose: str
    environment: str = "LAB"
    status: str = "ACTIVE"

@dataclass(frozen=True)
class CredentialRef:
    credential_ref_id: str
    account_id: str
    vault_provider: str
    secret_ref: str
    scopes: tuple[str, ...] = ()
    expires_at: str | None = None

    def validate(self) -> None:
        if not self.secret_ref.strip():
            raise ValueError("secret_ref required")
        if any(token in self.secret_ref.lower() for token in ["password=", "token=", "secret="]):
            raise ValueError("secret values must not be embedded in secret_ref")

@dataclass(frozen=True)
class Connector:
    connector_id: str
    connector_type: str
    provider: str
    version: str
    permissions: tuple[str, ...] = ()
    cost_class: str = "ZERO"
    status: str = "DEFINED"

    def validate(self) -> None:
        if self.connector_type not in {"API","MCP","SCRIPT","BROWSER","COMPUTER_USE"}:
            raise ValueError("unsupported connector_type")

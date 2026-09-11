from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SecretRef:
    provider: str
    path: str

    def validate(self) -> None:
        if self.provider not in {"ENV", "GITHUB_SECRETS", "VAULT_REF"}:
            raise ValueError("unsupported secret provider")
        if not self.path or any(token in self.path.lower() for token in ("token=", "password=", "secret=")):
            raise ValueError("secret values must not be embedded in references")


class EnvVaultAdapter:
    """LAB adapter: resolves only authorized environment-variable references."""

    def resolve(self, ref: SecretRef) -> str:
        ref.validate()
        if ref.provider != "ENV":
            raise PermissionError("this adapter resolves ENV references only")
        value = os.environ.get(ref.path)
        if value is None:
            raise KeyError(ref.path)
        return value


def redact(value: str) -> str:
    if not value:
        return ""
    return "***REDACTED***"

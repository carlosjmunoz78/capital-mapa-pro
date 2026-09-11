from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


FORBIDDEN_SECRET_FIELDS = {"password", "passwords", "token", "tokens", "api_key", "api_keys", "secret", "secret_value", "raw_secret"}


@dataclass(frozen=True)
class MakeConnectionRef:
    connection_id: int
    label: str
    app: str
    status: str
    credential_visibility: str


class CredentialRegistry:
    """Metadata-only credential registry.

    Raw credentials MUST live in an external secret provider (Supabase Vault,
    Make-managed connections, environment secrets, etc.), never in this file.
    """

    def __init__(self, payload: dict):
        self.payload = payload
        self.validate()

    @classmethod
    def from_path(cls, path: str | Path) -> "CredentialRegistry":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def validate(self) -> None:
        # Structural guard: explicit secret-bearing keys are forbidden anywhere.
        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key.lower() in FORBIDDEN_SECRET_FIELDS:
                        raise ValueError(f"raw secret field forbidden in registry: {key}")
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(self.payload)

        connections = self.payload.get("make_connections", [])
        ids = [int(row["connection_id"]) for row in connections]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate Make connection_id")
        for row in connections:
            if row.get("credential_visibility") != "OPAQUE_MANAGED_BY_MAKE":
                raise ValueError("Make connection credentials must remain opaque")

        for row in self.payload.get("secrets", []):
            if row.get("raw_value_stored_here") is not False:
                raise ValueError("registry secret entries must explicitly deny raw storage")
            vault_ref = row.get("vault_ref")
            if vault_ref is not None and not str(vault_ref).startswith("VAULT_REF:"):
                raise ValueError("vault_ref must be an opaque VAULT_REF")

    def connection(self, connection_id: int) -> MakeConnectionRef:
        for row in self.payload.get("make_connections", []):
            if int(row["connection_id"]) == int(connection_id):
                return MakeConnectionRef(
                    connection_id=int(row["connection_id"]),
                    label=str(row["label"]),
                    app=str(row["app"]),
                    status=str(row["status"]),
                    credential_visibility=str(row["credential_visibility"]),
                )
        raise KeyError(connection_id)

    def connections_for_app(self, app: str) -> tuple[MakeConnectionRef, ...]:
        return tuple(
            self.connection(int(row["connection_id"]))
            for row in self.payload.get("make_connections", [])
            if row.get("app") == app
        )

    def duplicate_label_candidates(self) -> dict[tuple[str, str], tuple[MakeConnectionRef, ...]]:
        """Return same-app/same-label groups for live usage audit.

        Matching labels are only candidates for consolidation. This method never
        treats them as safe-to-delete because consumer usage must be verified in
        Make before any connection is retired.
        """
        groups: dict[tuple[str, str], list[MakeConnectionRef]] = defaultdict(list)
        for row in self.payload.get("make_connections", []):
            ref = self.connection(int(row["connection_id"]))
            groups[(ref.app, ref.label)].append(ref)
        return {
            key: tuple(sorted(rows, key=lambda item: item.connection_id))
            for key, rows in groups.items()
            if len(rows) > 1
        }

    def incomplete_audit_scopes(self) -> tuple[str, ...]:
        """List audit scopes that are not explicitly AUDITED yet."""
        return tuple(
            scope
            for scope, state in self.payload.get("audit_scope", {}).items()
            if not str(state).startswith("AUDITED")
        )

    def secret_reference(self, credential_id: str) -> str | None:
        for row in self.payload.get("secrets", []):
            if row.get("credential_id") == credential_id:
                return row.get("vault_ref")
        raise KeyError(credential_id)

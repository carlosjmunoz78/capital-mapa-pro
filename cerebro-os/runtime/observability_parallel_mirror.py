from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

REQUIRED_SCOPE = ("company_id", "engine_id", "environment", "version")
SUPPORTED_LEGACY_SOURCES = {
    "activity_log": "log",
    "daily_report_snapshots": "metric",
    "document_intelligence_runs": "metric",
    "lead_events": "log",
    "notification_state": "incident",
    "runtime_policies": "log",
}


@dataclass(frozen=True)
class MirrorEnvelope:
    company_id: str
    engine_id: str
    environment: str
    version: str
    kind: str
    name: str
    payload: dict
    evidence_ref: str
    cost_eur: float = 0.0

    def validate(self) -> None:
        values = (self.company_id, self.engine_id, self.environment, self.version, self.kind, self.name, self.evidence_ref)
        if any(not str(value).strip() for value in values):
            raise ValueError("mirror envelope missing required scope or evidence field")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("unsupported environment")
        if self.kind not in {"log", "metric", "incident"}:
            raise ValueError("unsupported observability kind")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be dict")
        if self.cost_eur < 0:
            raise ValueError("cost_eur must be non-negative")


def build_parallel_envelope(*, source_table: str, scope: Mapping[str, str], name: str, payload: dict, evidence_ref: str, cost_eur: float = 0.0) -> MirrorEnvelope:
    if source_table not in SUPPORTED_LEGACY_SOURCES:
        raise ValueError("unsupported legacy source")
    missing = tuple(field for field in REQUIRED_SCOPE if not str(scope.get(field, "")).strip())
    if missing:
        raise ValueError(f"missing multiempresa scope: {','.join(missing)}")
    envelope = MirrorEnvelope(
        company_id=str(scope["company_id"]),
        engine_id=str(scope["engine_id"]),
        environment=str(scope["environment"]),
        version=str(scope["version"]),
        kind=SUPPORTED_LEGACY_SOURCES[source_table],
        name=name,
        payload={"legacy_source": source_table, "legacy_payload": dict(payload)},
        evidence_ref=evidence_ref,
        cost_eur=float(cost_eur),
    )
    envelope.validate()
    return envelope


def mirror_to_store(store, envelope: MirrorEnvelope) -> int:
    """Mirror into an auxiliary store only; never writes back to legacy App/CRM tables."""
    envelope.validate()

    class StoreEvent:
        company_id = envelope.company_id
        engine_id = envelope.engine_id
        environment = envelope.environment
        version = envelope.version
        kind = envelope.kind
        name = envelope.name
        payload = envelope.payload
        evidence_ref = envelope.evidence_ref
        cost_eur = envelope.cost_eur

        @staticmethod
        def validate():
            envelope.validate()

    return store.append(StoreEvent())


def assess_parallel_mirroring() -> dict:
    return {
        "legacy_source_count": len(SUPPORTED_LEGACY_SOURCES),
        "required_scope": REQUIRED_SCOPE,
        "legacy_tables_modified": False,
        "parallel_auxiliary_sink_only": True,
        "lab_mirroring_implementation_ready": True,
        "prod_mirroring_enabled": False,
        "prod_per_engine_coverage_proven": False,
        "rollback_strategy": "disable_mirror_without_touching_legacy_sources",
        "additional_subscription_required": False,
        "automatic_prod_promotion_allowed": False,
        "status": "PARALLEL_MIRROR_IMPLEMENTED_LAB_PROD_DISABLED",
    }

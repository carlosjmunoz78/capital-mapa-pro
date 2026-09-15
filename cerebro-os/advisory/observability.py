from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
from statistics import mean

from .gateway import ADVISORY_EXECUTE_PERMISSION
from .models import CANONICAL_HUMAN_EXCEPTIONS


@dataclass(frozen=True)
class ExecutionTelemetry:
    correlation_id: str
    company_id: str
    case_id: str
    engine_id: str
    environment: str
    status: str
    latency_ms: int
    confidence: float
    error_code: str | None = None
    audit_refs: tuple[str, ...] = ()
    cost_eur: Decimal = Decimal("0")

    def validate(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.correlation_id,
                self.company_id,
                self.case_id,
                self.engine_id,
                self.environment,
                self.status,
            )
        ):
            raise ValueError("telemetry identity fields required")
        if self.environment not in {"LAB", "PREPROD", "PROD"}:
            raise ValueError("invalid environment")
        if self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.cost_eur < 0:
            raise ValueError("cost_eur cannot be negative")

    def structured_log(self) -> dict[str, object]:
        self.validate()
        payload = asdict(self)
        payload["cost_eur"] = str(self.cost_eur)
        return payload


class TelemetryCollector:
    def __init__(self) -> None:
        self._records: list[ExecutionTelemetry] = []

    def emit(self, record: ExecutionTelemetry) -> None:
        record.validate()
        self._records.append(record)

    def records(self) -> tuple[ExecutionTelemetry, ...]:
        return tuple(self._records)

    def metrics(self) -> dict[str, object]:
        latencies = [record.latency_ms for record in self._records]
        errors = sum(record.error_code is not None for record in self._records)
        return {
            "executions": len(self._records),
            "errors": errors,
            "error_rate": (errors / len(self._records)) if self._records else 0.0,
            "latency_ms_avg": mean(latencies) if latencies else 0.0,
            "latency_ms_max": max(latencies) if latencies else 0,
            "cost_eur_total": str(sum((record.cost_eur for record in self._records), Decimal("0"))),
        }


def advisory_health() -> dict[str, object]:
    """Cheap deterministic liveness/readiness signal for the Advisory capability."""

    canonical = tuple(sorted(CANONICAL_HUMAN_EXCEPTIONS))
    ready = len(canonical) == 8 and ADVISORY_EXECUTE_PERMISSION == "advisory:execute"
    return {
        "liveness": "GREEN",
        "readiness": "GREEN" if ready else "RED",
        "human_exception_codes": canonical,
        "execute_permission": ADVISORY_EXECUTE_PERMISSION,
        "additional_cost_target_eur": 0,
    }

from dataclasses import dataclass

GREEN = "GREEN"
RED = "RED"
HUMAN_REQUIRED = "HUMAN_REQUIRED"

@dataclass(frozen=True)
class EngineHealth:
    engine_id: str
    tests_green: bool
    evaluation_green: bool
    tribunal_green: bool
    rollback_ready: bool
    observability_ready: bool
    human_required: bool = False

    @property
    def state(self) -> str:
        if self.human_required:
            return HUMAN_REQUIRED
        checks = (
            self.tests_green,
            self.evaluation_green,
            self.tribunal_green,
            self.rollback_ready,
            self.observability_ready,
        )
        return GREEN if all(checks) else RED

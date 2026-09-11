from dataclasses import dataclass

GREEN = "GREEN"
RED = "RED"
HUMAN_REQUIRED = "HUMAN_REQUIRED"
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}
REQUIRED_EVIDENCE = ("tests", "evaluation", "tribunal", "rollback", "observability")


@dataclass(frozen=True)
class EngineHealth:
    engine_id: str
    tests_green: bool
    evaluation_green: bool
    tribunal_green: bool
    rollback_ready: bool
    observability_ready: bool
    human_required: bool = False
    company_id: str = "GLOBAL"
    environment: str = "LAB"
    evidence_refs: tuple[str, ...] = ()

    @property
    def state(self) -> str:
        if not self.engine_id.strip() or not self.company_id.strip():
            return RED
        if self.environment not in VALID_ENVIRONMENTS:
            return RED
        if self.human_required:
            return HUMAN_REQUIRED
        checks = (
            self.tests_green,
            self.evaluation_green,
            self.tribunal_green,
            self.rollback_ready,
            self.observability_ready,
        )
        if not all(checks):
            return RED
        # Every positive health dimension must be backed by one concrete ref.
        # Positional refs keep this lightweight while preventing boolean-only GREEN.
        refs = tuple(ref for ref in self.evidence_refs if isinstance(ref, str) and ref.strip())
        return GREEN if len(refs) >= len(REQUIRED_EVIDENCE) else RED

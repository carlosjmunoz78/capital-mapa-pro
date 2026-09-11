from dataclasses import dataclass

STATES = ("DEFINED", "LAB_GREEN", "PREPROD_GREEN", "PROD_CANDIDATE", "PROD", "BLOCKED")
PROD_EVIDENCE_KEYS = (
    "contracts",
    "permissions",
    "tests",
    "evaluation",
    "tribunal",
    "observability",
    "rollback",
    "backup",
    "rebuild",
    "cost",
    "policy",
    "tenant_isolation",
)


@dataclass
class PromotionState:
    state: str = "DEFINED"

    def transition(
        self,
        target: str,
        *,
        gates_green: bool,
        rollback_verified: bool,
        backup_verified: bool,
        evidence_refs: dict[str, str] | None = None,
    ):
        if target not in STATES:
            raise ValueError("invalid promotion state")
        if target in {"PREPROD_GREEN", "PROD_CANDIDATE", "PROD"} and not (
            gates_green and rollback_verified and backup_verified
        ):
            raise ValueError("promotion gates not satisfied")

        if target in {"PROD_CANDIDATE", "PROD"}:
            refs = evidence_refs or {}
            missing = tuple(key for key in PROD_EVIDENCE_KEYS if not str(refs.get(key, "")).strip())
            if missing:
                raise ValueError(f"production promotion evidence missing: {missing}")

        allowed = {
            "DEFINED": {"LAB_GREEN", "BLOCKED"},
            "LAB_GREEN": {"PREPROD_GREEN", "BLOCKED"},
            "PREPROD_GREEN": {"PROD_CANDIDATE", "BLOCKED"},
            "PROD_CANDIDATE": {"PROD", "BLOCKED"},
            "PROD": {"BLOCKED"},
            "BLOCKED": {"DEFINED", "LAB_GREEN"},
        }
        if target not in allowed[self.state]:
            raise ValueError("invalid transition")
        self.state = target
        return self.state

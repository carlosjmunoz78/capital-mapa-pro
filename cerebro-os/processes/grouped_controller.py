from __future__ import annotations

MACRO_LOOPS: dict[str, tuple[str, ...]] = {
    "LOOP-25-COMMS": ("notifications", "voice", "post_sale", "referrals", "reporting"),
    "LOOP-26-PROPERTY": ("property_registry", "payments_sla_blocks", "agenda_third_parties"),
    "LOOP-27-STRATEGY": ("strategy_innovation", "expansion_ventures"),
}

MACRO_ORDER = ("LOOP-25-COMMS", "LOOP-26-PROPERTY", "LOOP-27-STRATEGY")
VALID_ENVIRONMENTS = {"LAB", "PREPROD", "PROD"}


class GroupedProcessController:
    def __init__(self, *, company_id: str = "GLOBAL", environment: str = "LAB") -> None:
        if not company_id.strip():
            raise ValueError("company_id required")
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError("invalid environment")
        self.company_id = company_id
        self.environment = environment
        self._family_status = {
            family: "PENDING"
            for macro in MACRO_ORDER
            for family in MACRO_LOOPS[macro]
        }
        self._evidence: dict[str, tuple[str, ...]] = {family: () for family in self._family_status}

    def update_family(self, family: str, status: str, *, evidence_refs=(), company_id: str | None = None, environment: str | None = None) -> None:
        if family not in self._family_status:
            raise ValueError("unknown process family")
        if status not in {"GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED", "IN_PROGRESS"}:
            raise ValueError("invalid family status")
        if company_id is not None and company_id != self.company_id:
            raise ValueError("cross-company update denied")
        if environment is not None and environment != self.environment:
            raise ValueError("cross-environment update denied")
        refs = tuple(ref for ref in evidence_refs if isinstance(ref, str) and ref.strip())
        if status == "GREEN" and not refs:
            raise ValueError("GREEN requires evidence_refs")
        self._family_status[family] = status
        self._evidence[family] = refs if status == "GREEN" else ()

    def macro_status(self, macro: str) -> str:
        if macro not in MACRO_LOOPS:
            raise ValueError("unknown macro loop")
        families = MACRO_LOOPS[macro]
        states = tuple(self._family_status[f] for f in families)
        if all(s == "GREEN" and self._evidence[f] for s, f in zip(states, families)):
            return "GREEN"
        if "BLOCKED" in states:
            return "BLOCKED"
        if "HUMAN_REQUIRED" in states:
            return "HUMAN_REQUIRED"
        if "RED" in states:
            return "RED"
        return "IN_PROGRESS"

    def next_macro(self) -> str | None:
        for macro in MACRO_ORDER:
            if self.macro_status(macro) != "GREEN":
                return macro
        return None

    def system_status(self) -> str:
        statuses = tuple(self.macro_status(m) for m in MACRO_ORDER)
        if all(status == "GREEN" for status in statuses):
            return "GREEN"
        if "BLOCKED" in statuses:
            return "BLOCKED"
        if "HUMAN_REQUIRED" in statuses:
            return "HUMAN_REQUIRED"
        if "RED" in statuses:
            return "RED"
        return "IN_PROGRESS"

    def snapshot(self) -> dict[str, dict]:
        return {
            family: {
                "status": status,
                "evidence_refs": self._evidence[family],
                "company_id": self.company_id,
                "environment": self.environment,
            }
            for family, status in self._family_status.items()
        }

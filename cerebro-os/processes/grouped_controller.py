from __future__ import annotations

MACRO_LOOPS: dict[str, tuple[str, ...]] = {
    "LOOP-25-COMMS": ("notifications", "voice", "post_sale", "referrals", "reporting"),
    "LOOP-26-PROPERTY": ("property_registry", "payments_sla_blocks", "agenda_third_parties"),
    "LOOP-27-STRATEGY": ("strategy_innovation", "expansion_ventures"),
}

MACRO_ORDER = ("LOOP-25-COMMS", "LOOP-26-PROPERTY", "LOOP-27-STRATEGY")


class GroupedProcessController:
    def __init__(self) -> None:
        self._family_status = {
            family: "PENDING"
            for macro in MACRO_ORDER
            for family in MACRO_LOOPS[macro]
        }

    def update_family(self, family: str, status: str) -> None:
        if family not in self._family_status:
            raise ValueError("unknown process family")
        if status not in {"GREEN", "RED", "BLOCKED", "HUMAN_REQUIRED", "IN_PROGRESS"}:
            raise ValueError("invalid family status")
        self._family_status[family] = status

    def macro_status(self, macro: str) -> str:
        if macro not in MACRO_LOOPS:
            raise ValueError("unknown macro loop")
        states = tuple(self._family_status[f] for f in MACRO_LOOPS[macro])
        if all(s == "GREEN" for s in states):
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
        return "GREEN" if all(self.macro_status(m) == "GREEN" for m in MACRO_ORDER) else "IN_PROGRESS"

    def snapshot(self) -> dict[str, str]:
        return dict(self._family_status)

from dataclasses import dataclass
from typing import Mapping, Iterable


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    old_output: Mapping[str, object]
    new_output: Mapping[str, object]
    required_equal_fields: tuple[str, ...]
    forbidden_new_truthy_fields: tuple[str, ...] = ("external_action_allowed",)


@dataclass(frozen=True)
class ReplayResult:
    total: int
    passed: int
    failed_cases: tuple[str, ...]
    green: bool


def compare_case(case: ReplayCase) -> bool:
    for field in case.required_equal_fields:
        if case.old_output.get(field) != case.new_output.get(field):
            return False
    for field in case.forbidden_new_truthy_fields:
        if bool(case.new_output.get(field)):
            return False
    return True


def compare_replay(cases: Iterable[ReplayCase]) -> ReplayResult:
    rows = tuple(cases)
    failed = tuple(case.case_id for case in rows if not compare_case(case))
    return ReplayResult(
        total=len(rows),
        passed=len(rows) - len(failed),
        failed_cases=failed,
        green=bool(rows) and not failed,
    )

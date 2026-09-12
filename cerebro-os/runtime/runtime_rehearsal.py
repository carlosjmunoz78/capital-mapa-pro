from dataclasses import dataclass

from cutover_gate import rollback_required
from facebook_caller_map import FACEBOOK_V3_TARGETS, router_references_superseded_legacy


@dataclass(frozen=True)
class RuntimeRehearsalResult:
    boot_green: bool
    route_map_green: bool
    rollback_trigger_green: bool
    external_action_safe: bool

    @property
    def green(self) -> bool:
        return all((
            self.boot_green,
            self.route_map_green,
            self.rollback_trigger_green,
            self.external_action_safe,
        ))


def run_rehearsal() -> RuntimeRehearsalResult:
    boot_green = bool(FACEBOOK_V3_TARGETS)
    route_map_green = not router_references_superseded_legacy()
    external_action_safe = all(not target.external_action_allowed for target in FACEBOOK_V3_TARGETS.values())

    # Prove the rollback decision path itself is executable and fail-closed.
    rollback_trigger_green = (
        rollback_required(
            new_health_green=False,
            parity_green=True,
            unexpected_external_action=False,
        )
        and rollback_required(
            new_health_green=True,
            parity_green=False,
            unexpected_external_action=False,
        )
        and rollback_required(
            new_health_green=True,
            parity_green=True,
            unexpected_external_action=True,
        )
        and not rollback_required(
            new_health_green=True,
            parity_green=True,
            unexpected_external_action=False,
        )
    )

    return RuntimeRehearsalResult(
        boot_green=boot_green,
        route_map_green=route_map_green,
        rollback_trigger_green=rollback_trigger_green,
        external_action_safe=external_action_safe,
    )


if __name__ == "__main__":
    result = run_rehearsal()
    print(
        "CEREBRO_RUNTIME_REHEARSAL",
        f"boot_green={result.boot_green}",
        f"route_map_green={result.route_map_green}",
        f"rollback_trigger_green={result.rollback_trigger_green}",
        f"external_action_safe={result.external_action_safe}",
        f"green={result.green}",
    )
    raise SystemExit(0 if result.green else 1)

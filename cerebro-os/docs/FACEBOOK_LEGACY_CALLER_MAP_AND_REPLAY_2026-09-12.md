# Facebook legacy caller-map + replay — 2026-09-12

## Scope
Legacy Make scenarios under controlled supersession:
- 9530582 -> 9531078 -> `runtime/facebook_link_preflight.py`
- 9528450 -> 9530484 -> `runtime/facebook_text_direct_preflight.py`
- 9532848 -> 9533424 -> `runtime/facebook_video_short_preflight.py`

## Evidence observed in Make
All three legacy scenarios are currently **inactive**, with `incompleteExecutions=0`, and are scheduled/read-only preflight/audit flows. Their inspected blueprints contain Notion/Data Store/HTTP-read modules only and no Facebook mutation module. They do not expose on-demand input interfaces and therefore are not treated as active callable runtime endpoints.

### 9530582
- trigger: scheduled every 7200 s
- dependencies: Notion connection 14347958 + Data Store
- behavior: query TEST `Texto + enlace`, read OP/calendar, register URL/program-count evidence
- external platform state: `FACEBOOK_NOT_CALLED`
- replacement V2 9531078 additionally reads Programming directly

### 9528450
- trigger: scheduled every 7200 s
- dependencies: Notion connection 14347958 + Data Store
- behavior: query pending Facebook text + OP, register governance evidence
- external platform state: `NOT_CALLED`
- replacement V2 9530484 expands direct evidence to publication + OP + calendar + programming

### 9532848
- trigger: scheduled every 7200 s
- dependencies: Notion + HTTP HEAD + Data Store
- historical description explicitly says V1 is inactive, was blocked by Calendar access and must not be reused as V2
- replacement V2 9533424 captures the complete direct evidence set and remains fail-closed

## Caller-map conclusion
**STATIC_CALLER_MAP_GREEN_FOR_SELF_TRIGGERED_LEGACY** for the inspected Make blueprints: each OLD is an inactive scheduled self-triggered audit/preflight, not an on-demand callable engine. No inbound caller is declared by its own contract.

This is not proof that no external system anywhere references the numeric scenario id. Therefore physical deletion remains blocked until repository/config search, Make cross-scenario dependency evidence and rollback gates are all complete.

## Replay
`runtime/fixtures/facebook_legacy_replay.json` records deterministic OLD-vs-NEW safety fixtures for the three supersessions. Tests require equality of the preserved safety semantics and reject any NEW fixture that enables an external action.

Current replay scope is **SAFETY_PARITY_GREEN**, not full live-data parity. It proves preserved non-mutation / TEST / platform-not-called invariants. It does not by itself authorize deletion or PROD promotion.

## Retirement gates
Retirement remains fail-closed and requires all of:
1. caller map complete across known repositories/configuration and Make dependencies;
2. replay parity green for required behavior;
3. rollback proven;
4. replacement runtime live in target environment.

Until all four are evidenced, OLD remains conserved.

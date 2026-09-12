# CEREBRO OS · Make scenario decision matrix · 2026-09-12

Purpose: canonical scenario-by-scenario architectural decision register. This file does not replace the evidence audit; it records the target role after evidence review. States are conservative and are never interpreted as permission to activate a mutator.

Allowed target states:
- `KEEP_ACTIVE`
- `KEEP_INACTIVE_READY`
- `GREEN_QUARANTINED`
- `WRAP_WITH_CEREBRO`
- `MIGRATE_TO_RUNTIME`
- `REPLACE_AFTER_PARITY`
- `RETIRE_CANDIDATE`

| scenario_id | current role | evidence status | target state | decision |
|---:|---|---|---|---|
| 9597710 | GSC 30d -> Notion inventory | active, healthy historical runs | KEEP_ACTIVE | Keep Make as GSC SaaS edge while connector value and cost remain good; CEREBRO consumes canonicalized data. |
| 9550706 | GSC weekly surveillance | active, successful automatic run evidence | KEEP_ACTIVE | Keep as low-cost own-data collector until equivalent runtime path beats connector maintenance/cost. |
| 9768402 | inbound social lead -> App/CRM mutation | config secure; runtime auth proof pending real event | WRAP_WITH_CEREBRO | Keep current production route, but all policy/idempotency/action governance belongs to Gateway. Never synthetic-run for evidence. |
| 9534096 | Instagram analytics capture | active, healthy connections | WRAP_WITH_CEREBRO | Connector edge may stay; normalized signals/history move to CEREBRO contracts/storage. |
| 9534088 | Instagram reconciliation/learning | active, healthy connections | MIGRATE_TO_RUNTIME | Reconciliation/learning is shared deterministic logic and should leave Make after parity. |
| 9523007 | LinkedIn analytics capture | active, healthy connections | WRAP_WITH_CEREBRO | Keep connector edge where useful; CEREBRO owns contract/history. |
| 9405249 | LinkedIn reconciliation/learning | active, healthy connections | MIGRATE_TO_RUNTIME | Reconciliation/learning belongs in shared runtime after parity. |
| 9527242 | universal reconciliation | active datastore-only, repeated success | MIGRATE_TO_RUNTIME | Deterministic shared logic should run in CEREBRO runtime, preserving OLD until parity. |
| 9705138 | network watchdog T-72/T-48 | active, successful recent runs | WRAP_WITH_CEREBRO | Preserve alert edge while supervisor/observability becomes canonical owner. |
| 9533690 | Facebook control/analytics master, no publication | active, successful recent runs | WRAP_WITH_CEREBRO | Preserve connector capture; progressively migrate decision/reconciliation logic to runtime. |
| 9597297 | Facebook comments -> opportunities RADAR | inactive; own-account signal | WRAP_WITH_CEREBRO | Use only as connector edge once canonical consumer and measured credit cost are ready. |
| 9595955 | Instagram comments -> opportunities RADAR | inactive; own-account signal | WRAP_WITH_CEREBRO | Same: connector edge only; canonical `own_social_signal` runtime contract exists. |
| 9597307 | LinkedIn comments -> opportunities RADAR | inactive; own-account signal | WRAP_WITH_CEREBRO | Keep inactive until consumer/cost gate; normalize through runtime adapter. |
| 9597372 | LinkedIn engagement -> intelligence RADAR | inactive; own-account signal | WRAP_WITH_CEREBRO | Good low-volume connector candidate if credits per useful signal are favorable. |
| 9597332 | YouTube comments -> opportunities RADAR | inactive; own-account signal | WRAP_WITH_CEREBRO | Keep inactive until consumer/cost gate; normalize through runtime adapter. |
| 9557377 | SEO competitive URLs/funnels/cannibalization | inactive; Notion/subscenario processor, not external collector | MIGRATE_TO_RUNTIME | Preserve OLD only for parity; competitive analysis/composition logic moves to CEREBRO. |
| 9557396 | SEO omnichannel/competition/support content | inactive; Notion/subscenario processor, not external collector | MIGRATE_TO_RUNTIME | Preserve OLD only for parity; no claim of competitor collection. |
| 9537817 | Notion -> social dispatcher | inactive; reads Notion, writes Data Store/feeder only | MIGRATE_TO_RUNTIME | Routing belongs in Gateway/runtime. Notion can remain source edge if useful. |
| 9535463 | ADS router/preflight | inactive; datastore-only; budget/QA/human gates | MIGRATE_TO_RUNTIME | Preserve as OLD reference; policy/budget authorization belongs in Gateway/policy. |
| 9524837 | idempotency and Run ID | inactive; datastore-only scheduled logic | MIGRATE_TO_RUNTIME | Idempotency is a shared runtime invariant and must not depend on Make Data Store. Preserve OLD until contract parity. |
| 9525004 | Facebook validation/normalization | inactive; Notion + datastore, human/elegibility gate | MIGRATE_TO_RUNTIME | Normalization and eligibility policy belong in CEREBRO; Make/Notion may remain edge inputs only. |
| 9533976 | Facebook Story preflight/queue | inactive; datastore-only; vertical/QA/asset checks | MIGRATE_TO_RUNTIME | Preflight/queue policy belongs in Gateway/runtime. Keep OLD for parity; no publication path is present. |
| 9533982 | universal multimedia request | inactive; datastore-only factory request contract | MIGRATE_TO_RUNTIME | Request orchestration belongs in Engine Factory/runtime. Preserve interface semantics while migrating. |
| 9533988 | Facebook long-video preflight | inactive; HTTP + datastore; no publication | MIGRATE_TO_RUNTIME | Media/preflight checks are deterministic policy and should live in Gateway/runtime; retain OLD for parity. |
| 9533589 | Facebook image receipt normalizer | inactive; explicitly integrated into active master 9533690 | RETIRE_CANDIDATE | Preserve until dependency proof confirms no direct callers; do not activate beside master. |
| 9537708 | YouTube processing verification | inactive; YouTube connector + datastore | WRAP_WITH_CEREBRO | Make may remain connector edge for platform processing status; canonical state/evidence belongs in CEREBRO. |
| 9534002 | video-generation adapter | inactive datastore-only factory adapter | MIGRATE_TO_RUNTIME | Adapter orchestration belongs in Engine Factory/model/tool router; Make should not be canonical runtime. |
| 9534003 | editing/subtitles adapter | inactive datastore-only factory adapter | MIGRATE_TO_RUNTIME | Editing/subtitle orchestration belongs in Engine Factory/tool runtime; preserve interface semantics for parity. |
| 9533999 | presenter/avatar adapter | inactive datastore-only factory adapter | MIGRATE_TO_RUNTIME | Presenter/avatar orchestration belongs in Engine Factory/model/tool router, not Make Data Store. |
| 9533998 | TTS voice adapter | inactive datastore-only factory adapter | MIGRATE_TO_RUNTIME | TTS routing belongs in Model/Tool Router with policy/cost controls; Make is not canonical runtime. |
| 9528458 | Facebook publications-without-OP detector | inactive; Notion + datastore, never publishes | MIGRATE_TO_RUNTIME | Missing-OP detection and technical blocking are deterministic governance logic and belong in Gateway/runtime. |
| 9531133 | Facebook image direct preflight V2 | inactive; Notion/HTTP validation, no publication | MIGRATE_TO_RUNTIME | Contract/asset/HTTP validation belongs in shared runtime after parity. |
| 9533424 | Facebook short-video direct preflight V2 | inactive; Notion/HTTP validation, no publication | MIGRATE_TO_RUNTIME | Deterministic preflight belongs in Gateway/runtime; keep OLD for contract parity only. |
| 9531078 | Facebook text/link direct preflight V2 | inactive; Notion validation, no publication | MIGRATE_TO_RUNTIME | Deterministic policy belongs in Gateway/runtime. |
| 9528450 | Facebook text-publication preflight audit | inactive; read-only Notion/datastore | RETIRE_CANDIDATE | Preserve while dependency map is checked; equivalent validation belongs in runtime and should not remain a parallel scheduled component. |
| 9694499 | legacy PREPROD WordPress secure transport | inactive fail-closed | REPLACE_AFTER_PARITY | Core Guard/Gateway is WordPress-primary. Retire only after OLD vs NEW parity and rollback proof. |
| 9694504 | legacy PREPROD WordPress safe reader | inactive fail-closed | REPLACE_AFTER_PARITY | Replace by Core Guard read abilities after live parity evidence. |
| 9694471 | WordPress write-verify-rollback TEST | inactive mutator | REPLACE_AFTER_PARITY | Core Guard now carries draft/update/snapshot/rollback code path; preserve quarantine until parity. |
| 9556936 | WordPress SEO internal correction | inactive mutator | REPLACE_AFTER_PARITY | Migrate operation to Core Guard/Gateway policy path. |
| 9694633 | WordPress readback TEMP | inactive reader | REPLACE_AFTER_PARITY | Replace with Core Guard inspection API after live parity. |
| 9681890 | Córdoba WordPress PROD correction TEMP | inactive PROD mutator | GREEN_QUARANTINED | Never reactivate ad hoc; equivalent controlled Core Guard path is target. |
| 9681887 | Córdoba WordPress PROD read TEMP | inactive reader | REPLACE_AFTER_PARITY | Replace with Core Guard inspection API after parity. |
| 9721021 | Drive -> WordPress CDN -> Notion | inactive external mutator | WRAP_WITH_CEREBRO | Keep Make only for Drive/Notion connector edge if valuable; WordPress mutation must be Core Guard/Gateway-governed. |
| 9721363 | base64 JPEG -> WordPress | inactive mutator | REPLACE_AFTER_PARITY | Core Guard has validated JPEG upload path; preserve OLD until live parity. |
| 9542046 | duplicate WordPress page as draft | inactive mutator | REPLACE_AFTER_PARITY | Core Guard duplicate-draft ability exists; retire only after live parity. |
| 9540674 | WordPress footer correction TEST | inactive mutator | GREEN_QUARANTINED | One-off/historical mutator; do not reactivate without explicit current requirement and rollback. |
| 9556822 | reconstruct SEO landing draft | inactive mutator | REPLACE_AFTER_PARITY | Core Guard draft/update path is target. |
| 9551114 | extract WordPress drafts | inactive reader | REPLACE_AFTER_PARITY | Core Guard `list-page-drafts` is code/CI green; live parity still required. |
| 9557305 | WordPress REST route inspector TEMP | inactive diagnostic | RETIRE_CANDIDATE | Retain until Core Guard capability map/live evidence closes diagnostic need. |
| 9538815 | direct WordPress -> Notion NO USAR | inactive historical | GREEN_QUARANTINED | Historical direct route; do not reactivate. |
| 9533997 | temporary paid-AI image adapter | inactive; explicitly migrate-to-native/not PROD | MIGRATE_TO_RUNTIME | Paid AI in Make is not default; native/local/router path preferred. |
| 9535460 | TikTok router/preflight | inactive datastore-only | MIGRATE_TO_RUNTIME | Shared route/preflight belongs in Gateway; platform connector edge can be added separately when needed. |
| 9537662 | YouTube router/preflight | inactive datastore-only | MIGRATE_TO_RUNTIME | Shared route/preflight belongs in Gateway. |
| 9522560 | LinkedIn router/preflight | inactive datastore-only | MIGRATE_TO_RUNTIME | Shared route/preflight belongs in Gateway. |
| 9528432 | Facebook format router V1 | inactive historical component | RETIRE_CANDIDATE | Superseded/integrated; preserve until dependency map confirms no callers. |
| 9530604 | Facebook direct format router V2 | inactive historical, explicitly superseded | RETIRE_CANDIDATE | Do not reactivate; remove only after dependency proof. |
| 9533499 | Facebook universal direct router V3 | inactive | MIGRATE_TO_RUNTIME | Routing logic belongs in Gateway/runtime. |
| 9533991 | Facebook universal format router V4 | inactive datastore-only | MIGRATE_TO_RUNTIME | Routing logic belongs in Gateway/runtime. |
| 9534074 | Instagram universal format router | inactive datastore-only | MIGRATE_TO_RUNTIME | Routing logic belongs in Gateway/runtime. |
| 9527140 | master router V1 | inactive datastore-only | MIGRATE_TO_RUNTIME | Central routing belongs in CEREBRO Gateway. |
| 9527162 | universal logs V1 | inactive datastore-only | MIGRATE_TO_RUNTIME | Heavy/canonical observability must not depend on Make Data Store. |
| 9534092 | Instagram health | inactive live despite historical ACTIVE description; read-only | KEEP_INACTIVE_READY | Can be re-evaluated as connector health edge, but supervisor/observability is canonical owner. |
| 9537719 | YouTube analytics capture | inactive | WRAP_WITH_CEREBRO | Connector edge candidate; history/normalization belongs in CEREBRO. |
| 9537722 | YouTube reconciliation | inactive | MIGRATE_TO_RUNTIME | Reconciliation belongs in shared runtime. |
| 9528246 | Facebook base analytics capture | inactive historical; integrated into 9533690 | RETIRE_CANDIDATE | Preserve until dependency proof; do not activate beside master. |
| 9528392 | Facebook analytics window generator | inactive historical; integrated into 9533690 | RETIRE_CANDIDATE | Preserve until dependency proof; do not duplicate master. |
| 9533995 | Facebook expanded organic analytics | inactive datastore-only | MIGRATE_TO_RUNTIME | Analytics transformation logic belongs in runtime if still needed. |

## Group rules already evidenced

All TEST scenarios explicitly named `DEPRECATED`, `NO USAR`, legacy staging/dry-run/gates/publicadores remain `GREEN_QUARANTINED` unless a replacement dependency audit promotes them to `RETIRE_CANDIDATE`. Current TEST publicadores are not activation candidates simply because their static contract looks safe. WordPress is Core Guard/Gateway first. Social/API connectors may remain Make edge only when connector value exceeds runtime maintenance cost. Strategic scoring, policy, budget, tribunal, reconciliation, logging and source-of-truth storage belong in CEREBRO.

## Remaining

This matrix is intentionally incremental. TEST 120/120 and CORE 62/62 unique-row closure remains `PARCIAL`; no global-green claim is allowed until every unique scenario id is represented or explicitly grouped by a complete, evidenced partition.
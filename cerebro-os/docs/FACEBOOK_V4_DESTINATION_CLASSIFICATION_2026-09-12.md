# FACEBOOK V4 DESTINATION CLASSIFICATION — 2026-09-12

Scope: Make scenario `9533991 · FENIX · CORE · Facebook · Router universal formatos · V4` and its seven logical destinations. This document is evidence/classification only. It does not activate or authorize PROD publication.

## Current classification

| V4 format | Destination | Current Make status | External mutator | Action |
|---|---:|---|---|---|
| Texto orgánico simple | 9533715 | inactive | `facebook-pages:CreatePost` | KEEP_INACTIVE + WRAP_WITH_CEREBRO_GUARD |
| Texto + enlace | 9533724 | inactive | `facebook-pages:CreatePost` | KEEP_INACTIVE + WRAP_WITH_CEREBRO_GUARD |
| Imagen | 9533532 | inactive | `facebook-pages:UploadPhoto` | KEEP_INACTIVE + WRAP_WITH_CEREBRO_GUARD |
| Vídeo corto | 9533564 | inactive | `facebook-pages:uploadAReel` | KEEP_INACTIVE + WRAP_WITH_CEREBRO_GUARD |
| Carrusel | 9533967 | inactive | `facebook-pages:CreatePostWithPhotos` | KEEP_INACTIVE + WRAP_WITH_CEREBRO_GUARD |
| Vídeo largo | 9533972 | inactive | `facebook-pages:UploadVideo` | KEEP_INACTIVE + WRAP_WITH_CEREBRO_GUARD |
| Story | 9533976 | inactive | none | MIGRATE_TO_RUNTIME / preflight only |

All six mutating destinations are real PROD-capable Make adapters but are currently inactive. None was activated or executed during this audit.

## Guard implemented in CEREBRO runtime

`runtime/facebook_prod_mutator_guard.py` inventories the six mutators and fails closed unless the complete execution evidence is present: multi-company scope, PROD environment, engine enabled, one-time override, record match, non-expired authorization, idempotency clear, explicit publication authorization, policy green, target runtime live, rollback proven, and T-48 evidence where the OLD contract already requires it.

Even when every machine gate is green, the guard returns `READY_FOR_EXPLICIT_EXECUTION` with `external_action_allowed=false` and `human_reason=SIGNATURE_REQUIRED`. Therefore the deterministic runtime cannot silently turn routing readiness into a real Facebook mutation.

## OLD contracts preserved

- `9533724` requires final URL, UTM required, allowed domain, approved production/calendar/programming, one-time override, idempotency and T-48 before `CreatePost`.
- `9533532` requires approved image asset, production/calendar/programming, one-time override, idempotency, legal/brand QA and T-48 before download + `UploadPhoto`.
- `9533564` requires approved vertical MP4, minimum 540x960, duration 3–90 s, production/calendar/programming, one-time override and idempotency before `uploadAReel`.
- `9533967` requires publish engine enabled, one-time override, matching publication, no prior idempotency record, `authorized=true`, and 2–30 photos before `CreatePostWithPhotos`.
- `9533972` requires publish engine enabled, one-time override, matching publication, no prior idempotency record and `authorized=true` before `UploadVideo`.
- `9533976` has no Facebook connector. It only validates a vertical Story candidate and queues/prepares it; it remains non-mutating.

## Status

- Classification: GREEN.
- Runtime mutator guard: GREEN_CODE_CI.
- Make PROD adapters: EXISTING / INACTIVE / PRESERVED.
- PROD autonomous execution: BLOCKED by policy and evidence gates.
- Human exception required for real publication: `SIGNATURE_REQUIRED`.

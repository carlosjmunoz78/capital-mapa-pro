# Supabase PROD · session context caller closure · 2026-09-18

Status: PARCIAL · all currently discovered ACTIVE Edge Function callers migrated except one guarded backfill surface. SECURITY global remains fail-closed.

Project: `fenix-capital-prod` (`cluhljgonannaafpmblx`).

## Objective

Retire direct authenticated calls to `public.fenix_prod_session_context()` without breaking App/CRM/Notion/document workflows. The replacement pattern is:

`Bearer -> auth.getUser() -> service_role -> fenix_prod_actor_context_by_auth_server(p_auth_user_id)`

No SQL ACL has been revoked in this block.

## Exhaustive ACTIVE Edge Function source inventory

A source-level inventory covered 42 ACTIVE Supabase Edge Functions. Exact direct-RPC detection distinguished `fenix_prod_session_context()` from the supported server wrapper `fenix_prod_session_context_server(...)`.

The original direct-caller set discovered during the closure loop was:

1. `fenix-b2b-actions`
2. `fenix-ana-knowledge`
3. `fenix-ana-canonical`
4. `fenix-memory-api`
5. `fenix-evidence-api`
6. `fenix-ana-api`
7. `fenix-document-intelligence-test`
8. `fenix-document-intelligence`
9. `fenix-document-extract`
10. `fenix-communications-gateway`
11. `fenix-document-reread`
12. `fenix-document-auto-ingest`
13. `fenix-document-existing-backfill`

The gateway string `fenix_prod_session_context_server` is not counted as a direct legacy caller.

## Live migrated callers

Previously completed and preserved:
- `fenix-b2b-actions` -> v10, SHA-256 `057dc41b86de5a3dcc059f58249dde16424e1b19937ead891f2bfebf5e610884`
- `fenix-ana-knowledge` -> v10, SHA-256 `970beb8876a3ad657124fc28038cb040a42d3fa8ffd9f2ee2bcc07ce6ec66ce2`
- `fenix-ana-canonical` -> v10, SHA-256 `dc9c251a248c0151efbfe87f3a53b072c6650ea97592e5825c493d6ea999d5da`
- `fenix-ana-api` -> v11, SHA-256 `b657f7336fb7baac4fce236f2158c778ccd896a742c87d378ece44c744ce0cc5`

Completed in this closure block:
- `fenix-memory-api` v9 -> v10, SHA-256 `e96ec1aeb63be03028a9c342453969058c1144d664bcf25f080542e010f96c18`
- `fenix-evidence-api` v13 -> v14, SHA-256 `e60f373ac261bff2ffda161397f67bfcaa5b4a93797a42f8e19bcc02ebe8675d`
- `fenix-document-intelligence-test` v8 -> v9, SHA-256 `d8f1945b692225c139155765e866c66fed740e94b6775f6148fa3a6ee6cae5ae`
- `fenix-document-intelligence` v12 -> v13, SHA-256 `9f3c9042711d64fe071dd8c5ddd76867c51652c773a0b1158538270457872947`
- `fenix-document-extract` v12 -> v13, SHA-256 `29000645966a35e2553cc575d4ec0e8221ec811cbc9226389921fa4c9a542a3f`
- `fenix-communications-gateway` v8 -> v9, SHA-256 `a4a24b8218c37bd19e929db852f28c99f75765769918e17d99e4964025a23942`
- `fenix-document-reread` v2 -> v3, SHA-256 `25770f17e07b51c9c574e8f69e3062396ba91e6b8900f655cb835fc588042d4a`
- `fenix-document-auto-ingest` v2 -> v3, SHA-256 `50af0b9cb947b46c467d699559d0b123541214e936ed4bf4437fddb2f4ab7a2e`

All of the above were live-source re-read after deployment and no longer contain an exact direct call to `fenix_prod_session_context()`.

## Rollback / preservation

Exact repository snapshots exist for the migrated surfaces where captured before deployment, including:
- `fenix-b2b-actions-v9.ts`
- `fenix-ana-knowledge-v9.ts`
- `fenix-ana-canonical-v9.ts`
- `fenix-ana-api-v10.ts`
- `fenix-memory-api-v9.ts`
- `fenix-evidence-api-v13.ts`
- `fenix-document-intelligence-test-v8.ts`
- `fenix-document-intelligence-v12.ts`
- `fenix-document-extract-v12.ts`

For the other changed Edge Functions, the immutable pre-change version number and SHA-256 are recorded above and remain the rollback anchor in Supabase deployment history. No claim is made that an exact repository source snapshot exists where it was not physically captured.

## Remaining direct caller

`fenix-document-existing-backfill` remains ACTIVE v7 with SHA-256 `049c41052556d38a4860369143aa04e455344067a0b584d46cb728bb75a9ec39` and still directly calls `fenix_prod_session_context()`.

A deployment-only authentication refactor was prepared, but the current execution channel blocked deployment under its safety controls. No backfill operation was executed and no data was changed.

Therefore:
- `authenticated EXECUTE` on `fenix_prod_session_context()` MUST NOT be revoked yet;
- the legacy ACL remains a compatibility gate for this one ACTIVE function;
- no bulk revoke is authorized.

## HTTP E2E gate

Authenticated HTTP E2E remains required before ACL retirement. This execution channel does not expose a reusable real-user bearer token, so authenticated production-route E2E is still `POR_AUDITAR`.

## Safety statement

This block does not declare SECURITY green, global autonomy, or PROD promotion. It changed authentication plumbing only on the listed Edge Functions and did not rewrite App/CRM business rows, RLS policies, SQL function bodies, or promotion flags.

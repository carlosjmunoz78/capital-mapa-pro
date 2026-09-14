# Supabase SECURITY DEFINER — remaining 16 final classification · 2026-09-14

State after successful retirement of the first 8 legacy authenticated RPCs.

## Verified current state

- Supabase Security Advisor SECDEF warning count: 16 (down from 24).
- The 8 retired legacy RPCs have `authenticated EXECUTE = false` and retain `service_role EXECUTE = true`.
- Current App default-branch GitHub code search for `fenix_prod_` returns no indexed direct RPC callers. Treat this as conservative evidence only, not proof of absence in historical/external clients.
- Live `fenix-app-gateway` v17 continues to use server-only wrappers.

## Group A — read/session capabilities (7)

1. `fenix_prod_ana_knowledge_answer_user(text)` — PRESERVE / WRAP. No server wrapper currently evidenced.
2. `fenix_prod_chat_conversations_user()` — PRESERVE / WRAP. No server wrapper currently evidenced.
3. `fenix_prod_chat_list_v2_user(text,integer)` — PRESERVE / WRAP. No server wrapper currently evidenced.
4. `fenix_prod_chat_people_user()` — PRESERVE / WRAP. No server wrapper currently evidenced.
5. `fenix_prod_profile_get_user()` — PRESERVE until full-profile parity exists. `fenix_prod_profile_get_server(text)` exists but returns a smaller profile contract and is therefore NOT parity.
6. `fenix_prod_profile_socials_get_user()` — PRESERVE / WRAP. No server wrapper currently evidenced.
7. `fenix_prod_session_context()` — RETIRE CANDIDATE after authenticated route parity. `fenix_prod_session_context_server(text)` exists and the live App Gateway exposes `/session/context`, but no fresh authenticated HTTP parity proof for this exact route is recorded in this checkpoint.

## Group B — mutating capabilities (9)

1. `fenix_prod_chat_attachment_add_user(...)` — PRESERVE / WRAP; legacy duplicate candidate only after V2 parity.
2. `fenix_prod_chat_attachment_add_v2_user(...)` — PRESERVE / WRAP; preferred attachment semantics.
3. `fenix_prod_chat_conversation_create_user(...)` — PRESERVE / WRAP.
4. `fenix_prod_chat_group_create_user(...)` — PRESERVE / WRAP.
5. `fenix_prod_chat_send_v2_user(...)` — PRESERVE / WRAP/CONSOLIDATE.
6. `fenix_prod_contact_create_v2(...)` — PRESERVE / WRAP; richer multi-email/multi-phone contract than current Gateway contact route.
7. `fenix_prod_inmo_followup_update_v1(...)` — PRESERVE / WRAP; dedicated follow-up capability absent from current generic Gateway update route.
8. `fenix_prod_profile_socials_update_user(jsonb)` — PRESERVE / WRAP; current profile API does not expose social updates.
9. `fenix_prod_profile_update_user(jsonb)` — RETIRE CANDIDATE only after full-profile parity is proven. Existing `fenix_prod_profile_update_server(text,text,text)` is NOT contract-equivalent: it covers only display name / zone and cannot replace the richer self-service RPC without App capability loss.

## Internal dependency check

Live DB function-definition scan found only two references among the remaining set:

- `fenix_prod_profile_update_user` calls `fenix_prod_profile_get_user`.
- `fenix_prod_session_context_server` references `fenix_prod_session_context` semantics internally/by equivalent contract.

No other database-function references to the remaining 16 were found in the scanned public/fenix_prod definitions.

## Decision

- Immediate revoke now: **0/16**.
- Retire candidates after exact parity/E2E: **2/16** (`session_context`, `profile_update_user`).
- Preserve and wrap before retirement: **14/16**.

This is intentional. The remaining warnings represent capabilities that may have been bypassed or lost during the App migration. Revoking them simply to reduce an advisor count would violate the project rule CONSERVAR → ENTENDER → ENVOLVER → PROBAR → MEJORAR → MIGRAR.

## Next implementation order

1. Wrap read-only session/knowledge/chat/profile-social routes behind server wrappers and the existing Gateway.
2. Restore conversation-aware chat and attachment routes in parallel, with OLD-vs-NEW tests.
3. Add V2 contact and inmobiliaria follow-up server contracts.
4. Add full-profile/social server parity before any profile RPC retirement.
5. Run authenticated browser E2E and only then selectively revoke direct `authenticated EXECUTE`.

No direct-user capability is revoked by this evidence update.
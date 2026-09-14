# Supabase SECURITY DEFINER mutator disposition · 2026-09-14

Scope: the 9 mutating/review-required user RPCs previously classified in the 24-function SECURITY DEFINER set. No grants or function definitions are changed by this document.

## Evidence used

- Live `fenix-app-gateway` v17 was inspected.
- Live `fenix-profile-api` v1 was inspected.
- Current GitHub code searches across `fenix-capital-inmo-map` and `capital-mapa-pro` returned no indexed callers for the 9 exact RPC names.
- Negative code search is conservative evidence only; it does not prove absence from old bundles, external clients, or historical deployments.

## Disposition

### WRAP — preserve capability, move behind authenticated server/gateway contract before retirement

1. `fenix_prod_chat_attachment_add_user(...)`
   - No indexed current caller found.
   - No equivalent chat-attachment route exists in live `fenix-app-gateway` v17.
   - Action: WRAP before any revoke; likely App functionality candidate to recover during post-migration App repair.

2. `fenix_prod_chat_attachment_add_v2_user(...)`
   - No indexed current caller found.
   - No equivalent chat-attachment route exists in live gateway.
   - Action: WRAP; prefer V2 semantics if retained, then retire older duplicate only after parity evidence.

3. `fenix_prod_chat_conversation_create_user(...)`
   - No indexed current caller found.
   - Live gateway only exposes legacy `/chat` list/send and has no conversation-create route.
   - Action: WRAP; treat as potential lost App capability, not dead code.

4. `fenix_prod_chat_group_create_user(...)`
   - No indexed current caller found.
   - No group-create route exists in live gateway.
   - Action: WRAP; preserve until App OLD-vs-NEW audit establishes whether group chat must be restored.

5. `fenix_prod_chat_send_v2_user(...)`
   - No indexed current caller found.
   - Live gateway sends through `fenix_prod_chat_send_server`, not conversation-aware V2.
   - Action: WRAP/CONSOLIDATE; do not retire until V2 conversation semantics are either restored behind server RPC or explicitly proven obsolete.

6. `fenix_prod_contact_create_v2(...)`
   - No indexed current caller found.
   - Live gateway `/contactos` POST calls `fenix_prod_contact_create_server`, whose request surface carries one email and one phone; V2 RPC signature supports richer multi-email/multi-phone payloads.
   - Action: WRAP; flag as probable migration capability gap to check during App repair.

7. `fenix_prod_inmo_followup_update_v1(...)`
   - No indexed current caller found.
   - Live gateway has generic inmobiliaria update but does not expose the dedicated follow-up notes / next-contact contract represented by this RPC.
   - Action: WRAP; flag as probable migration capability gap.

8. `fenix_prod_profile_socials_update_user(jsonb)`
   - No indexed current caller found.
   - Live `fenix-profile-api` supports profile GET and PATCH for display name / zone, but no socials update route.
   - Action: WRAP; preserve capability and include in App profile audit.

### RETIRE CANDIDATE — only after deployed-caller and rollback gates

9. `fenix_prod_profile_update_user(jsonb)`
   - No indexed current caller found.
   - Live `fenix-profile-api` v1 already performs authenticated user validation, resolves the actor server-side, and calls `fenix_prod_profile_update_server` for profile updates.
   - Action: RETIRE CANDIDATE, not immediate revoke. Gate on authenticated browser parity, deployed-caller=0 evidence, and rollback SQL.

## Result

- KEEP direct user-callable: 0/9
- WRAP / preserve capability: 8/9
- RETIRE candidate after gates: 1/9
- Immediate revoke authorized: 0/9

This disposition intentionally favors preserving capabilities because the App migration is known to require an OLD-vs-NEW recovery audit. The next App phase should use these eight WRAP items as an explicit checklist of functionality that may have been lost or bypassed during migration.

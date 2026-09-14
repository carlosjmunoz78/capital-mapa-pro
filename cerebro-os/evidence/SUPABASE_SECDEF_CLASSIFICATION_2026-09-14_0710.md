# Supabase SECURITY DEFINER classification · 2026-09-14 07:10 Europe/Madrid

Read-only classification of the 24 live `public` SECURITY DEFINER functions still executable by `authenticated` in project `cluhljgonannaafpmblx`. No grants were changed.

## Exact partition

### A. Migrated legacy targets — 8

These are the already-known RPCs whose APP callers were migrated behind `fenix-app-gateway` and whose selective retirement SQL + rollback is prepared. Retirement remains gated on safe authenticated HTTP E2E and write-path rollback evidence.

- `fenix_prod_chat_list_user(integer)`
- `fenix_prod_chat_send_user(text,text)`
- `fenix_prod_contact_create(...)`
- `fenix_prod_exp_create(...)`
- `fenix_prod_exp_update(...)`
- `fenix_prod_notifications_list_user(integer)`
- `fenix_prod_notification_mark_user(uuid,text)`
- `fenix_prod_sign_create(...)`

### B. Read/session surfaces — 7

Live definitions contain read/select behavior and no direct INSERT/UPDATE/DELETE token in the inspected definition. This is classification evidence, not authorization to retain them indefinitely.

- `fenix_prod_ana_knowledge_answer_user(text)`
- `fenix_prod_chat_conversations_user()`
- `fenix_prod_chat_list_v2_user(text,integer)`
- `fenix_prod_chat_people_user()`
- `fenix_prod_profile_get_user()`
- `fenix_prod_profile_socials_get_user()`
- `fenix_prod_session_context()`

### C. Mutating/review-required surfaces — 9

Live definitions contain mutating DML and require caller/route/semantic review before any grant change:

- `fenix_prod_chat_attachment_add_user(...)`
- `fenix_prod_chat_attachment_add_v2_user(...)`
- `fenix_prod_chat_conversation_create_user(...)`
- `fenix_prod_chat_group_create_user(...)`
- `fenix_prod_chat_send_v2_user(...)`
- `fenix_prod_contact_create_v2(...)`
- `fenix_prod_inmo_followup_update_v1(...)`
- `fenix_prod_profile_socials_update_user(jsonb)`
- `fenix_prod_profile_update_user(jsonb)`

A default-branch GitHub code search for these nine exact names returned no current matches. That negative search is conservative evidence only: it does not prove absence from generated bundles, external clients, historical deployments or non-indexed code. Therefore these nine remain fail-closed under caller review.

## Security consequence

The 24 warnings are no longer an undifferentiated set:

- 8 = selective retirement candidates after HTTP gate.
- 7 = likely intentional client read/session APIs, must be reviewed by contract rather than blindly revoked.
- 9 = mutators requiring explicit caller/route parity review.

Blind bulk revoke remains forbidden. Current blocker remains `HUMAN_REQUIRED: HIGH_RISK` for establishing a safe dedicated authenticated PROD identity if no already-authorized test principal is found.
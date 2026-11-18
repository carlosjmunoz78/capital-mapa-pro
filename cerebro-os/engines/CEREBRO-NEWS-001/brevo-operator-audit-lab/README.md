# NEWS001 · Brevo audit operator · isolate LAB
Read-only Supabase Edge Function `cerebro-news001-brevo-operator-audit-lab`. It uses **existing** project-level BREVO_API_KEY, never prints or returns it. Single `POST /audit` method with `x-news001-lab-token` equal to the dedicated random 256-bit secret generated and encrypted in Supabase Vault under `NEWS001_BREVO_OPERATOR_LAB_TOKEN_20261118`. Function stores only its SHA256 digest, never the secret. No exposed health/data pages. Signed privileged SQL `pg_net` invocation only, never frontend.

Exact allowlist for read GET `/emailCampaigns/112`, `/emailCampaigns/113`, `/smtp/templates/115`, `/smtp/templates?limit=50&offset=0`. Returns summaries only, no HTML body, contact data or secrets. NO write endpoint, NO campaign send, NO schedule, NO old workflow change.

Designed to verify live Brevo state, not replace Work or enlarge the custom connector. Future deployment **only in parallel**, nothing overwritten, no schedules or PROD App/CRM mutations. To rollback, remove only this dedicated Edge Function and vault secret by exact IDs after archive; do not delete the existing audit or transactional alerts.

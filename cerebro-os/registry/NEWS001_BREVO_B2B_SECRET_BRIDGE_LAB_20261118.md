NEWS001 Brevo B2B isolated read-only bridge, version 0.3.0, 2026-11-18.

HECHO code only in LAB branch. Pure JS module enumerates Brevo list IDs 9,13,12,6, deduplicates by ID, excludes Salinas and provider blocked, holds unknown company/blacklist; output only aggregates with no emails/names. Existing target lists B2B 18 and B2C 17, untouched. Source list membership never permits commercial sending.

Separate Supabase Edge candidate entrypoint index.ts is designed verify_jwt=true and NEWS001_BREVO_AUDIT_ENABLED flag OFF by default. Uses existing server-only BREVO_API_KEY environment; fails closed for unknown auth, no writes and no sends. Do not deploy before reviewing tests, account quotas and secured invocation. Never reanimate retired functions fenix-brevo-inventory-once, fenix-brevo-probe-once, or fenix-brevo-lead-webhook.

IMPORTANT: social-lead-ingest v5 writes default consentimiento_comercial false; existing plugin web form similarly unverified. Do not promote B2C automation until verified opt-ins and double confirmation. Productora images still QA HOLD. All App/CRM/WordPress PROD intact. No additional subscription.

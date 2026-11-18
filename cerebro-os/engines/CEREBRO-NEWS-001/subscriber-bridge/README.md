# NEWS-001 · CEREBRO Brevo opt-in bridge (LAB)

Independent of ChatGPT plugin. Reuses WordPress/CEREBRO ingest, maps explicitly opted-in private leads to #17 and agency leads to #18. Must be called only with server-side verified evidence; `proof_signature_verified` is a result of independent cryptographic verification, **not** an untrusted browser JSON field. Never turn it on based on user-submitted booleans.

By default: `NEWS001_CONTACT_SYNC_ENABLED=false`; no API calls, no welcome emails. Read-only preflight requires proof of backend-form origin, exact consent text version, opt-in timestamp, HMAC evidence, suppression checks and correct persona. Before any Brevo update GET contact and hold on any blacklist, list unsubscribe or cross-profile membership. Never clear an opt-out or change email.

Still needed before PROD: authenticated ingest adapter that verifies origin signature, streaming durable queue/idempotency, snapshot/rollback, public form E2E and one-click unsubscribe. No updates to WordPress PROD, App/CRM or automations #10/#11 are made in this PR.

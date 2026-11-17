# NEWS-001 · Brevo read-only API probe LAB · 17 November 2026

## Verifiable state
- Native connected Brevo UI is authenticated but the Opera read-only browser shows notifications/menu only at /contact/lists and does not expose the underlying list detail/actions. This does NOT prove there are zero lists.
- GitHub connector does not authorize Actions Secrets inventory (GET forbidden by connector).
- WordPress PROD active plugin list (read only) has NO active native Brevo/Sendinblue plugin.
- Supabase PROD Vault metadata query returned NO secret NAME containing brevo/sendinblue/smtp/newsletter. This does NOT prove that no credential is held in a different secret store.
- No existing Cloudflare Worker script with brevo/subscribe/email in name; old NEWS-001 Workers remain separately isolated.
- No contact imported, list modified, campaign sent, API key exposed, or account subscribed.

## Candidate
`brevo_inventory_readonly.py`: Python standard-library read-only, private environmental secret only; exact GET allowlist for account, senders, contact lists and B2B agency list member counts. Strict 30-page limit, no retries, 10 s timeout, no arbitrary redirects, no API key in argv/query/logs. Report contains **only aggregate totals**, list names/IDs, active/blacklist counts; NEVER contacts' email addresses, names, or personal attributes.

Every agency list remains NOT SENDABLE even if a contact is not blacklisted, because opt-in evidence and unsubscribe status must be verified independently. PREPROD lists never become PROD by inference. B2C historical contacts never imported. The credential-independent tests run automatically by GitHub Actions on LAB branch; **live probe still requires an existing Brevo API key to be securely connected** and a deliberate single read-only execution; do not solicit raw key in chat. Recommended scope if Brevo offers OAuth: account:read and contacts:read; a generic API key may be broader, so only use the worker with enforced GET allowlist.

The official Brevo API is https://developers.brevo.com/reference/get-lists, https://developers.brevo.com/reference/get-contacts-from-list, https://developers.brevo.com/reference/get-account, https://developers.brevo.com/reference/get-senders. The list API is deprecating `totalSubscribers`/ `totalBlacklisted` fields, hence this probe uses paginated list-contacts data and counts. See API changelog 2026-10-14: `modifiedSince` does not equal opt-out event; always inspect current `emailBlacklisted`.

## Activation gates
- Attach credential via secret store with least privilege, not a public config variable and not into chat/GitHub files or logs.
- Verify access from bounded private runtime or explicit workflow with no stdout secrets.
- Run one read-only inventory probe and review anonymized counts/list IDs; reconcile with CRM B2B consent states using evidence, keep discrepancies in HOLD.
- Certify editorial/UMS image QA and then test DOI and welcome at internal authorized inboxes; do not enable production sends now.

## Secure manual inventory execution (not auto-triggered)
Workflow `.github/workflows/news001-brevo-inventory-readonly-lab.yml` now offers a separate gated `workflow_dispatch` input `confirm_readonly=AUDIT` on branch `cerebro-engine-factory-v0`. It passes `secrets.BREVO_API_KEY` only into its one-shot read-only job and prints only aggregated list/account data. Neither a push nor a default manual dispatch runs the API probe. If the secret is absent, it exits BLOCKED_BREVO_SECRET_MISSING with no network request. No API key or contact data should ever be entered into the chat or checked into GitHub files.

# NEWS001 · Weekly scheduler candidate · CEREBRO-only

Independent of ChatGPT and Brevo ChatGPT Plugin. Reuses the existing 10-block/13-link/two-image editor and `brevo-draft-factory/factory.mjs` unchanged. Runs via the already contracted GitHub Actions runtime; no paid AI dependency. **NOT DEPLOYED**.

- **Dry-run default:** `node weekly-orchestrator/cli.mjs editor/out`. This reads the latest CEREBRO generated report + HTMLs and makes **zero API calls**. Missing current verified official news intentionally blocks rendering.
- **Production path:** `NEWS001_MODE=schedule` + `NEWS001_SCHEDULE_ENABLED=true`, `BREVO_API_KEY` encrypted secret, `NEWS001_RELEASE_PROOF_PATH` pointing to a trusted production release document and independent `NEWS001_RELEASE_PROOF_SHA256`. All 15 gates must be green, cohort evidence current and free quota sufficient. Only then creates two scheduled campaigns through Brevo marketing API.
- **Schedule:** Thursday 10:30 for agencies, 11:00 for private consumers, Europe/Madrid incl. DST. Campaign names are unique by ISO week, and global Brevo campaign inspection aborts on duplicates before creating either.
- **Cannot autonomously send from this LAB branch:** GitHub `schedule` events only execute from the repository's **default** branch (`main`); we must not merge into `main` or enable live keys until OLD vs NEW, backups, rollback, E2E signup + unsubscribe, source freshness, images, quotas, and review pass. A protected Cloudflare Free weekly trigger could alternatively be promoted in a separate release.
- **Lead route:** `news001_onboarding_route.py` (same branch) remains LAB-only. It accepts one explicit marketing checkbox with backend evidence; generic `consent_privacy` must never imply newsletter opt-in. `fenix-cerebro-leads` existing PROD plugin/CRM remain untouched.
- **No changes** to Brevo #10/#11 welcome flows, old #8/#9 flows, campaigns #112/#113, WordPress PROD, App or CRM.

## Emergency kill-switch and rollback
`NEWS001_SCHEDULE_ENABLED=false` stops all future API mutations immediately. For already scheduled campaigns, disable or unschedule those specific new campaign IDs in Brevo following the release runbook. Do not touch old automations. Restore previous commit in isolated branch.
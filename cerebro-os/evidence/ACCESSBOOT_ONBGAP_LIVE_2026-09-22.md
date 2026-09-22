# ACCESSBOOT-001 / ONB-GAP-001 — live evidence and next block (2026-09-22)

## Scope and confirmed evidence

- Company: `fenix`; environment: `LAB`; version: `v0`. PROD remains off.
- Existing Browser Bridge local service: `1.4.1`. Do not replace or disrupt Chrome, the paired local service, the existing extension or the DPAPI-protected transport credential.
- GitHub PR #249: merged recovery of Windows transport; PR #250: merged zero-mutation `ACCESSBOOT_CAPABILITY_SNAPSHOT`; PR #251: merged live capability-gap evaluator; PR #252: merged parallel fixed-allowlist browser metadata policy contract.
- Real PREPROD snapshot command: `accessboot-capability-snapshot-20260922-1104`; delivered once and completed at `2026-09-22T11:04:35.912Z`; `semantic_verified=true`.
- Real snapshot returned `paired=true`, `chrome_running=true`, `extension_connected=true`, `extension_fresh=true`, `transport_online=true`, `kill_switch_enabled=true`, `browser_discovery_status=GREEN`, and 6 detected Chrome profiles. No raw secrets and no external mutation reported. The observed result is historical evidence of successful physical execution, not a perpetual claim of live readiness.
- PREPROD device heartbeat observed live at 11:09:25Z, age ~11 seconds.
- No authenticated website-session access was established by that snapshot. Do not infer login state, page access, tab metadata or desktop control from Chrome process/profile metadata.

## Engine and contract status

| Item | Status | Evidence/limitation |
|---|---|---|
| Windows Bridge transport recovery | CONFIRMED_OPERATIONAL | Real LAB roundtrip and metadata snapshot completed |
| ACCESSBOOT zero-mutation capability snapshot | CONFIRMED_OPERATIONAL | Durable PREPROD command/result and semantic receipt |
| ACCESSBOOT snapshot assessment | HECHO (code, CI) | PR #251; scope, freshness, no profile names in output |
| ONB-GAP fixed allowlist read-only metadata policy | DEFINIDO / code and tests | PR #252; no runtime dispatch or extension upgrade yet |
| Generic browser navigation | NOT_IMPLEMENTED | Must not be inferred from fixed localhost page test |
| Website title/URL readback | NOT_IMPLEMENTED | New extension sidecar and end-to-end semantic check needed |
| Generic page content reading | NOT_IMPLEMENTED | Must obtain distinct policy approval and domain controls |
| Windows UI automation / full PC control | NOT_IMPLEMENTED | Dedicated provider, per-action policy and readback needed |
| PROD autonomous browser/PC use | DISABLED | No promotion without PREPROD, backups and security review |

## Contract for next implementation block

`NEXT_BLOCK=ONB-GAP-READONLY-001`: implement the fixed-allowlist read-only browser metadata pilot without replacing the current working Bridge.

1. Preserve service `1.4.1`, extension `1.4.1`, transport recovery `1.4.3` and current DPAPI credential. Inventory live file placement and dependencies before any patch.
2. Build a parallel Chrome extension and local service/transport update path for a fixed `https://example.com/` pilot only, scoped to `fenix/LAB/v0`. Keep the existing `OPEN_LOCAL_TEST_PAGE` regression path working.
3. Accept only `READ_ONLY_PAGE_METADATA`. No forms, arbitrary domains, cookie/password extraction, private tab enumeration, payment, publishing, external writes, or PROD.
4. Verify the URL actually loaded and page title `Example Domain`; opening a tab alone does not satisfy semantic acceptance. Deny unexpected redirects.
5. Add native Windows 5.1 and mocked Chrome tests, cloud queue idempotency, denied-action and no-secret tests. Capture observability, backup and rollback.
6. Package and validate all machine-side changes before any additional physical step. Prefer one controlled installer; allow up to four manual steps only if strictly needed. Do not claim a deployed external-navigation capability until live LAB semantic receipt is stored.
7. Once fixed pilot is confirmed, design policy-scoped site discovery, authenticated-session inventory (metadata only), then Windows desktop provider separately. Keep prioritizing official APIs and connected app integrations over computer-use fallbacks.

## Safety and anti-loop

Never queue unimplemented `READ_ONLY_PAGE_METADATA` to the current 1.4.3 transport. It currently accepts only `OPEN_LOCAL_TEST_PAGE` and `ACCESSBOOT_CAPABILITY_SNAPSHOT`.

Do not assume a green CI result equals physical acceptance. Do not ask for the same installation again if the live snapshot has already succeeded. No WPVibe, no Make dependency, no new subscriptions, no PROD and no copying tokens, cookies or browser profile contents. Human exception only for the approved canonical reasons.

### Verification references

- Merged PRs: https://github.com/carlosjmunoz78/capital-mapa-pro/pull/249 , /250 , /251 , /252
- ACCESSBOOT snapshot command/result persisted in `public.cerebro_device_commands_preprod` and `public.cerebro_device_results_preprod`.
- Engine Factory verify on PR #251: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/35719824331 (success).
- Engine Factory postmerge #251: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/35719934841 (success).
- FORGE PREPROD postmerge #251: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/35719934960 (success).
- Engine Factory on PR #252: https://github.com/carlosjmunoz78/capital-mapa-pro/actions/runs/35720157580 (success).

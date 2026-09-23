# CEREBRO LAB v1.6.2 · post-reboot coexistence (staged)

## Evidence
After Windows restart, another CEREBRO service responded on `127.0.0.1:8765/health` with `version=0.2.0`, `status=OK`, `durable_queue=true`, not a Browser Bridge. 8766 initially refused connections. Manually executing existing `Start-CerebroBrowserBridge.ps1` restored GREEN/CONNECTED v1.6.2/cloud ONLINE. PREPROD heartbeat subsequently was fresh (~5 s). No source confirms why the other service owns 8765; do not kill it.

## Additive design
* User-level Task Scheduler task on interactive logon, 30-second delay; **does not replace any existing task**.
* Discover an already GREEN matching Fenix LAB Bridge across 8765..8785; if present exit without duplication. Otherwise launch the existing verified 1.4.1 service using `CEREBRO_BRIDGE_PORT=8766` only if 8766 is free. Fail closed on conflict; do not terminate or alter the service occupying 8765.
* Reuse installed v1.6.2 recovery target and existing credential. No new pairing, extension installation, registry modification, third-party subscriptions, PROD activation or credential transfer. The installed launcher already invokes the transport launcher; Chrome extension v1.6.2 scans 8765..8785.
* Registration is explicit, per-user, does not start anything immediately, and writes no existing Bridge files. Rollback unregisters only the verified task and preserves runtime files and current process.
* `autostart-v162-result.json` records next boot's selected port/status. Task Scheduler history and local Bridge health are independent corroboration.

## Physical gate
Only register after `/health` Bridge GREEN, extension 1.6.2 CONNECTED, cloud ONLINE, and no pending commands. Run `REGISTER_AUTOSTART.ps1` once in a trusted extracted package; verify task is present. On next **planned** reboot, wait for logon plus 30 seconds, then check `8766/health`, cloud heartbeat and no duplicate Bridge. Do not reboot just to test without user approval.

## Rollback
Run `ROLLBACK_AUTOSTART.ps1`. Restores previous startup behavior by removing only task owned by this package. Never delete existing task under same name if ownership cannot be verified.

CEREBRO Browser Bridge ACCESSBOOT capability patch 1.4.3

Extract this ZIP and double-click INSTALL_AND_VERIFY.bat once.
This patch updates only CerebroBrowserTransport.ps1.
It does not restart Chrome or replace the Browser Bridge service/extension.

New LAB/PREPROD-safe command:
- ACCESSBOOT_CAPABILITY_SNAPSHOT

The snapshot is metadata-only and reports no passwords, tokens, cookies, page content,
credential values, or external website mutations. PROD remains disabled.

Result: %LOCALAPPDATA%\CEREBRO\browser-bridge\recovery-v1.4.3.json
Rollback: double-click ROLLBACK.bat.

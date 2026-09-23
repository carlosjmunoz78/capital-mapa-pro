CEREBRO Browser Bridge · REBOOT AUTOSTART V0 · FENIX LAB ONLY

Purpose:
- Preserve the existing service currently observed on 127.0.0.1:8765.
- Start the Browser Bridge after Windows logon on a deterministic 127.0.0.1:8766.
- Reuse the existing v1.6.2 target, pairing, extension ID and DPAPI cloud credential.
- No administrator privileges, no Scheduled Task, no PROD, no credential copy.

Install:
1. Run INSTALL_AND_VERIFY.bat once.
2. Expected report:
   %LOCALAPPDATA%\CEREBRO\browser-bridge\reboot-autostart-v0.json
   status=GREEN, pinned_port_8766=true.
3. Reboot once for physical acceptance.
4. After login open Chrome Default and verify:
   http://127.0.0.1:8765/health = existing durable service (unchanged)
   http://127.0.0.1:8766/health = CEREBRO Browser Bridge 1.4.1 GREEN
   extension 1.6.2 CONNECTED and cloud transport ONLINE.

Rollback:
- Run ROLLBACK.bat. It removes the startup file and restores any prior file at the same path.

Safety:
- This package does not stop or modify the service on 8765.
- It does not install/reinstall the extension.
- It does not alter Supabase, CRM, App, WordPress or PROD.

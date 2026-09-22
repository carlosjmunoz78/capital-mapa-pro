CEREBRO Browser Bridge transport recovery 1.4.2

Extract this ZIP and double-click INSTALL_AND_VERIFY.bat once.
The installer locates the existing 1.4.1 package, backs up only changed scripts,
checks SHA256, stops only an existing transport worker, and launches the new worker.
It never restarts the Bridge, Chrome, or the extension.

Result: %LOCALAPPDATA%\CEREBRO\browser-bridge\recovery-v1.4.2.json
Acceptance: %LOCALAPPDATA%\CEREBRO\browser-bridge\acceptance-1.4.1.json
If pairing has expired or is absent, the result will state PAIRING_REQUIRED.
Do not reuse an expired pairing code. No pairing secret is included in this ZIP.

Double-click ROLLBACK.bat to restore the backed up files.
This package is LAB/PREPROD only. PROD is disabled.

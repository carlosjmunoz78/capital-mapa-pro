CEREBRO Browser Bridge v1.6.2 - PARALLEL LAB-ONLY MULTI-COMMAND LEDGER
STAGED TECHNICAL PACKAGE. Do not install while PR #271 is draft or CI/rollback acceptance incomplete.
For the EXISTING Fenix LAB Chrome Default profile only. Do not remove/reinstall extension:
its Chrome ID, pairing, transport credentials and browser state must be preserved.
First verify the physical v1.6.1 command terminal and absence of QUEUED commands.
A single old v1.6.1 receipt key cannot prove A->B->A replay safety; v1.6.2
adds a bounded persistent map of 128 command receipts (fail closed when full).
Pending CLAIMED receipts are ambiguous after a crash: NEVER reexecute without reconciliation.

After CI + explicit physical deployment gate:
1. Extract inner release ZIP; double-click INSTALL_AND_VERIFY.bat only once.
2. Expected PARTIAL until same Chrome extension is reloaded at chrome://extensions.
3. Inspect %LOCALAPPDATA%\\CEREBRO\\browser-bridge\\recovery-v1.6.2.json.
4. Verify /health GREEN, extension 1.6.2 CONNECTED and transport ONLINE.
5. Perform one same-command_id local receipt and tab-count test before cloud PREPROD.
6. Cloud PREPROD only after local correlation; do not enable PROD.
ROLLBACK.bat restores prior Bridge+extension files from v1.6.2 backup.
Original v1.6.1 installer and 1.6.1 unpacked backup remain untouched.
No embedded credentials; allowlisted localhost and https://example.com only.

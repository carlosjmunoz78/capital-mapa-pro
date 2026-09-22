CEREBRO Browser Bridge v1.6.1 - local-test replay guard (fenix LAB only).
Do not reactivate existing v1.6.0 extension while a QUEUED test is stuck.
This package installs a scoped service acceptance patch and v1.6.1 extension into
THE SAME unpacked extension directory. It preserves device identity, pairing and
DPAPI transport credentials. Only three source files are replaced after SHA256
verification and backup. No PROD activation or arbitrary websites.

1. Extract the ZIP completely (GitHub artifact may contain this ZIP as a second ZIP).
2. Run INSTALL_AND_VERIFY.bat. Expected status PARTIAL until Chrome reload.
3. Reload the EXISTING unpacked Chrome extension at chrome://extensions, do not remove it.
4. Verify extension v1.6.1 and receipt without clicking local queue multiple times.
5. If error, keep extension disabled and share recovery-v1.6.1.json.
ROLLBACK.bat restores the three previous files and launches the old Bridge.
Existing v1.6.0 package remains untouched. No secrets embedded.

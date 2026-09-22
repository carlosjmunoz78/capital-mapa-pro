CEREBRO Browser Operator recovery 1.6.0 - fenix LAB only.

INSTALL_AND_VERIFY.bat installs the parallel-validated service, transport,
and updated unpacked Chrome extension in the SAME installed extension
directory. It preserves pairing and Chrome extension identity and does not
activate PROD. The package hash-verifies each managed file and creates a
local full-file snapshot before changing anything.

After installer reports PARTIAL:
1. Open chrome://extensions and reload the existing CEREBRO extension.
2. Verify extension 1.6.0 CONNECTED and transport ONLINE.
3. Run remote LAB acceptance: the existing local-page test, fixed external
   example.com title/URL readback, then localhost fixture CLICK, TYPE,
   SELECT and READ with cloud receipts and semantic verification.

The installer must not mark GREEN before live remote physical acceptance.
If regression or other errors occur, run ROLLBACK.bat and restart prior Bridge.
Do not delete the original v1.5 package or the backup directory.

No passwords, payment data, arbitrary-origin access or PROD writes.
The operator manipulates only its deterministic localhost LAB fixture.

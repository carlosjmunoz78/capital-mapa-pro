CEREBRO BROWSER BRIDGE - LAB METADATA PILOT 1.5.0

This package updates only the existing LAB Browser Bridge service, transport, and the
contents of its existing unpacked chrome_extension_v1_4_1 folder. Service identity
remains 1.4.1; existing DPAPI credential and pairing state are never copied to this ZIP.
The Chrome extension folder PATH stays unchanged to preserve its extension ID.

Extract ZIP, double-click INSTALL_AND_VERIFY.bat once. When prompted, open
chrome://extensions and click Reload for the existing CEREBRO extension.
The installer reports PARTIAL until remote LAB semantic proof succeeds.

New action READ_ONLY_PAGE_METADATA is restricted to https://example.com/ and
checks loaded URL and title Example Domain. No cookies, login data, forms, page
content, arbitrary sites, or external writes. PROD is disabled. No extra subscriptions.

If any failure appears, report recovery-v1.5.0.json status/error (never secrets).
ROLLBACK.bat restores the four previous files from its snapshot; relaunch the
previous Bridge afterward if rolled back.

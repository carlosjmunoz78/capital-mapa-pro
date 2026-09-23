CEREBRO ACCESSBOOT WINDOWS OPERATOR V0

One-time bootstrap upgrade. After this upgrade, commands originate in the existing authenticated CEREBRO cloud queue.

Capabilities:
- FS_CREATE_DIRECTORY: only relative paths below the current user's Documents folder; blocks absolute paths, drive letters, traversal, UNC/double separators and invalid Windows filename characters; idempotent if directory exists.
- BROWSER_OPEN_URL: HTTPS only, no credentials in URL, default/443 port, localhost/private IPv4 blocked. Executed by extension 1.7.0 and verified by tab readback.
- Existing LAB actions preserved. PROD remains denied. No generic shell execution.

Acceptance orders from CEREBRO cloud (not installer): FS_CREATE_DIRECTORY relative_path Cerebro Zeus; BROWSER_OPEN_URL https://www.youtube.com/. Both require semantic_verified=true.

Installer: Install-CerebroAccessbootV0.ps1. Rollback uses the same script with -Rollback and restores its pre-install snapshot.

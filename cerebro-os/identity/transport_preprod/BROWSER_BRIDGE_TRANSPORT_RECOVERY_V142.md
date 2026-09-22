# Browser Bridge Windows transport recovery 1.4.2

## Scope

The service and Chrome extension stay at 1.4.1. This patch changes only the Windows PREPROD transport worker, its launch path, the package manifest, recovery installer, tests, and CI. The allowed remote action remains `OPEN_LOCAL_TEST_PAGE` in `fenix/LAB/v0`; PROD stays disabled.

## Root cause and evidence

The prior worker passed a Windows path such as `C:\...\curl-body.json` into a quoted `curl --config -` value. curl treats backslashes as escapes inside config values. The resulting `data-binary` path was invalid and curl exited with `option --config: error encountered when reading a file`. An isolated probe on Windows PowerShell 5.1 and PowerShell 7 reproduced exit 26 with the unescaped path and exit 0 after doubling backslashes. The physical worker log recorded the same config error at 10:55 local time on 2026-09-22.

The prior worker acquired the mutex before it created the runtime directory and before the fatal logging scope. The old launcher discarded the process handle and reported that the worker was ensured without checking whether it survived. These were observability defects that hid startup failures.

## Change

- Escape Windows backslashes in the curl config path; write request JSON in UTF-8 without BOM; read stdout and stderr concurrently.
- Use curl's widely supported `fail` option and report a structured exit code without echoing server output or secrets.
- Load the local transport key from its existing runtime file, keeping it out of the worker command line.
- Log startup, enrollment, reconnect, poll, command, failure, and exit phases as JSON records.
- Add a dedicated launcher that validates 8765..8785, scope, PID, early exit, stdout, stderr, and health.
- Add a one-click recovery package with SHA256 verification, timestamped backup, and automatic file rollback if launch fails.

## Security review

The gateway URL and local action are fixed. Scope is checked before enrollment and for each command. The remote action gate rejects anything other than `OPEN_LOCAL_TEST_PAGE`, and the result reports `external_mutation_performed=false`. Bearer and pairing values do not enter curl arguments or logs. curl config is delivered over stdin; temporary JSON bodies are in the current user's LOCALAPPDATA runtime and removed in `finally`. The bearer remains DPAPI protected at rest. Nonces and one-time pairing remain gateway contracts. The installer replaces only four named files and stops only a process identified as the transport worker; it leaves the Bridge, Chrome, extension, and unrelated processes running. The SHA256 manifest prevents a modified recovery payload from installing. No arbitrary URL, shell command, or desktop control was added.

An existing Bridge service launch path still passes its local key in its own process arguments. This pre-existing exposure is outside this transport patch and should receive a separate design review; the new worker launch does not add to it. The independent `public.cerebro_ci_runs_preprod` RLS advisory remains **POR AUDITAR / SECURITY DEBT**.

## Physical validation on 2026-09-22

The recovery installer was run on the Fénix Windows LAB PC against the existing 1.4.1 package. It saved a timestamped backup, reported `ONLINE`, and produced acceptance `GREEN` with all ten checks passing and `next_gate=REMOTE_LAB_ROUNDTRIP`. The current pairing was consumed once; the older expired pairing history was left intact. The PREPROD command `fenix-lab-roundtrip-c6341d2a-f2bd-40ef-a2fd-a873a4896931` was delivered once, completed by the Chrome extension, and stored with `semantic_verified=true`, `evidence_ref=LOCAL_TEST_PAGE_OPENED`, and `external_mutation_performed=false`.

## Rollback

`ROLLBACK.bat` stops only the transport worker and restores the four backed-up files. The installer performs the same restoration automatically if the new worker exits or its launch fails. The Bridge, Chrome, extension, PREPROD history, and DPAPI credential are preserved. After restoring an old worker, a valid consumed pairing cannot be reused; use the existing DPAPI credential or provision a fresh pairing through the approved PREPROD flow.

## Verification boundaries

Local Browser Bridge tests, Windows PowerShell 5.1 parse, curl UTF-8/path integration, package build, and physical LAB roundtrip passed. The full local Python suite has unrelated Windows SQLite file-handle cleanup failures in console/onboarding tests and a path-separator assertion in `test_three_loops_batch`; Engine Factory CI on Linux is the authoritative full-suite run. CEREBRO Engine Factory V0 and CEREBRO FORGE PREPROD must both be green before merge. Additional cost: 0 EUR.

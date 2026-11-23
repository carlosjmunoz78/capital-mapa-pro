# CP81 · Consumer inventory and promotion gate (LAB)

**Base**: CP80 `660c7908b1a7ef9e4a0bae2012acbace9bc5ff03`.

## Why
CP80 fails closed when `claim_attempts` is omitted on `OnboardingQueue.complete` or `retry_or_dead_letter`. A remote or hidden consumer using the old contract could stop working after deployment.

## Work delivered
Added `audit/onboarding_claim_consumer_inventory_cp81.py` and a unittest gate. They scan the Python source tree available in the actual checked-out branch, enumerate direct call sites, require the claim token on positive calls, separately recognize negative security tests, and flag dynamic `getattr(queue, 'complete')` for manual review. Output is JSON when invoked directly. CI runs the test, with no cron or runtime service.

**Static coverage limit**: does NOT prove other repositories, dynamically constructed methods, installed packages, external clients, Cloudflare Service Bindings, deployment identity, stored access tokens or actual process execution. The separate remote consumer inventory and real canary remain **POR AUDITAR**.

## Remote LAB read-only check
Existing Workers `cerebro-jarvis-lab-eu` and `cerebro-jarvis-cut32-lab-eu` have no direct Service Binding to FACT-001, and their JARVIS Gateway is OFF. The existing `cerebro-fact001-gateway-lab-eu-20261109` has internal NIA/Techscout/UMS bindings, but GATEWAY_ENABLED and ALLOW_MUTATIONS remain false. No E2E JARVIS→FACT claim is possible from those settings alone.

## Rollback
Revert this CP81 commit or reset only its LAB branch to the exact CP80 commit. Keep PR DRAFT, do not merge `main`, do not deploy into App/CRM or switch on any Gateway. No additional resource or paid service.

## Independent-process integration gate
`tests/test_onboarding_two_processes_cp81.py` starts separate Python OS processes against one isolated SQLite file. One scenario validates a lease expiration, second claimant and failed stale-writer completion, followed by valid completion by the new claimant. A second scenario starts two independent claimers concurrently and requires exactly one successful claim. No external API, PC server, paid resource, PROD or long-running runtime is involved. A GREEN CI run confirms only subprocess behavior inside a GitHub CI runner, not a distributed Cloudflare worker or persistent remote deployment.

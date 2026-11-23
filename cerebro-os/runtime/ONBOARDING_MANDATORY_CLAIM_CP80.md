# CP80 · Mandatory attempt fencing in OnboardingQueue LAB

CP77 added `claim_attempts` as an optional compatibility argument. Although the official worker always passed it, any legacy caller without it could still finalize another worker's reclaimed request using the latest attempts read inside the transaction. CP80 changes the two mutation APIs to fail closed if `claim_attempts` is absent, a bool, nonint or <=0. The public method signatures retain the optional argument position for migration diagnostics, but behavior intentionally changes: legacy no-token callers are blocked.

Internal consumers updated based on source inspection: CP69 connection-cleanup tests (3 calls), CP77 legacy test (now confirms rejection and successful tokened path), worker-service tests (2 calls). The official batch worker already passes the attempt token. 7 new CP80 regression tests. No schema, IAM, credential or remote deployment changes. Private LAB branch only. Any unlisted external consumers MUST be inventoried and adapted before integration/promotion; the compatibility break is not authorized for PROD.

Rollback to CP79 `c1090b2ff2775ef99be9f227f7e8b8c56f93e8e1`. CI is necessary but insufficient for real distributed fencing; add replay tests with two separately authenticated processes and remote persistent storage before autonomy. JARVIS Gateway OFF, Brevo 123–126 SUSPENDED, UMS publishing OFF.

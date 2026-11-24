# Owner admission PREPROD candidate

Status: CANDIDATE_LOCAL_TESTED; not part of deployed 1.1.0 artifact. No execution or promotion authority. Existing LAB console and six PREPROD Workers unchanged. Cloudflare Access policy owner-only and two historical accepted LAB authentications observed 23 November 2026. These do not certify PREPROD.

Candidate adapts the existing RS256 verification pattern, requires a distinct PREPROD audience, pinned owner subject and email, exact origin, app token and scoped fixture read route. JWTs are never persisted or returned. Local Node 22.16.0 tests 20/20 with synthetic RSA keys and mocked JWKS endpoint. Run `node --test cerebro-os/gateway/preprod-core/owner-admission/owner-admission.test.mjs`.

HOLD: verify real token claims and distinct audience; enforce bounded body streaming and failure handling at HTTP boundary; implement durable one-time reservation, signed receipt and issuer verification, dispatcher provenance propagation, full E2E, and fresh release build. Never trust an unsigned admission object as an authorization, never consume 001. No public route, deployment or billing changes. Rollback: revert this additive commit; deployed artifacts unaffected. Cost of this change: no new subscriptions. Billing certification remains pending.

# ADR DEC-20261127-03 — Private owner-operated CEREBRO OS

Status: accepted architectural scope; not a release approval.

CEREBRO OS is a private internal work system for a single human owner/operator. It is not offered as a SaaS, licensed, rented or sold to third parties. Multi-company support means the owner manages their own companies from the same console; it does not require a commercial multi-user product.

Keep distinct least-privilege machine/service identities, tenant and environment isolation, audit, budget controls, backup, recovery, rollback, and legally required human oversight. Existing business applications and CRM retain their users, permissions, responsibilities and data contracts. No migration or access revocation is authorized by this ADR.

Prioritize integration and gradual release of existing ordinary business capabilities that have independently passed their applicable gates. Do not introduce commercial sign-up, billing or third-party access features as launch requirements. Existing platform holds, internal release gates and provider controls remain effective. No deployment, new spending, credentials or permission changes are authorized solely by this document.

Release candidate baseline: PR 297, commit 2d68555582e681938783fea1f06079da96ed3c45. Preserve this baseline. This documentation-only change does not certify a different executable artifact or authorize release.

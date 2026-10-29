## 2026-04-22 — Rotate RFC 3161 TSA from freetsa.org to sectigo

Change type: High
Approved by: change board (2026-04-18), procurement officer (2026-04-19)
Author: A. Tan
Reviewers: M. Wong, S. Krishnan
Tested: staging bundle of 30 manifests, all verified under both TSAs

Behavior change:
- New manifests stamped by sectigo; freetsa kept as secondary for legacy
- Verifier accepts both TSA certs (archived under /etc/ssl/tsa/ both)
- Manifests from 2026-04-22 onward have REKOR-A and SECTIGO tsr files

Rollback: revert to freetsa; re-stamp the last 24h of manifests (requires
re-upload to WORM under new keys — see DR-3)

Post-deploy audit: 1h review showed no unexpected actions. First sectigo
stamp at 2026-04-22 14:11 UTC, verified at 14:13 UTC.

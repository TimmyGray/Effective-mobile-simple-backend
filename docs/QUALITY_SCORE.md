# Quality Metrics

<!-- Updated automatically by /audit-service and /sweep -->

Baseline captured during `/setup-workflow` on 2026-04-09.

## Test Summary

| Suite | Files | Tests | Pass Rate |
|-------|-------|-------|-----------|
| Backend (`manage.py test accounts`) | 1 | 31 | 100% |
| Frontend | N/A | N/A | N/A |
| **Total** | 1 | 31 | 100% |

## Lint / Type / Build

| Check | Errors | Warnings |
|-------|--------|----------|
| Backend Lint | NOT CONFIGURED | 0 |
| Frontend Lint | N/A | N/A |
| Backend Types | NOT CONFIGURED | 0 |
| Frontend Types | N/A | N/A |
| Backend Build | NOT CONFIGURED | 0 |
| Frontend Build | N/A | N/A |

## Dependencies

| Scope | Packages | Outdated | Vulnerabilities |
|-------|----------|----------|-----------------|
| Backend | NOT CONFIGURED | NOT CONFIGURED | NOT CONFIGURED |
| Frontend | N/A | N/A | N/A |

## Tech Debt Status

| Priority | Todo | Done |
|----------|------|------|
| Critical | 0 | 3 |
| High | 1 | 2 |
| Medium | 3 | 1 |
| Low | 2 | 0 |
| Features | 2 | 1 |

## Sweep History

<!-- Append entries here after each /sweep or /audit-service run -->
- 2026-04-09: Initial baseline established. Validation commands and dependency audits are not yet configured because application manifests are not present in repository root.
- 2026-04-09 (Phase 12 sweep): Cadence threshold met for sweep; removed unused `get_user_model` import in `accounts/admin_serializers.py`; `manage.py test accounts` — 31 passed. Audit and retrospective not due (counters 3/5 and 3/10).

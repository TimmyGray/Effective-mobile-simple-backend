# Execution Plan: B-M1 Auth & Authorization Decision Matrix Tests

## Task Description

Add automated tests for the authentication and authorization decision matrix: happy paths and denial edge cases for `decide()`, RBAC matrix, and HTTP `401`/`403` semantics.

## Acceptance Criteria

- Unit tests cover explicit deny/allow precedence, matrix grants, superuser role rules, and default deny.
- API tests assert `403` when per-user `AuthPolicyRule` denies `profile_update` or `logout` despite global allows.
- Stable `decide().reason` codes documented for `auth:*` actions used by views.

## Shipped

- https://github.com/TimmyGray/Effective-mobile-simple-backend/pull/8 (merged 2026-04-09).

## Key Files

- `accounts/tests.py` — `PolicyDecideTests` additions, `AuthzDecisionMatrixApiTests`
- `docs/exec-plans/tech-debt-tracker.md` — B-M1 marked done
- `docs/QUALITY_SCORE.md`, `docs/exec-plans/maintenance-cadence.json` — audit/sweep bookkeeping in same PR

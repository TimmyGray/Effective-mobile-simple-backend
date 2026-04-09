# Tech Debt & Feature Tracker

Machine-readable task backlog. Single source of truth for all work items.

## Task Format

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|

### ID Prefixes
- `FEAT-#` — New user-facing feature (area = fullstack or any)
- `B-C#` / `B-H#` / `B-M#` / `B-L#` — Backend tasks by priority (Critical/High/Medium/Low)
- `F-C#` / `F-H#` / `F-M#` / `F-L#` — Frontend tasks by priority

### Priority Levels
- **Critical** — Blocking production use
- **High** — High impact, clear need
- **Medium** — Improves quality, not urgent
- **Low** — Nice-to-have polish

### Effort Scale
| Effort | Guideline |
|--------|-----------|
| 0.1d | Config/doc-only changes |
| 0.25d | Single-file fixes |
| 0.5d | New hook/service, moderate refactor |
| 1d | New module, significant feature |
| 2d | Multi-module feature |
| 3d+ | Cross-cutting feature |
| 5d | Major feature |

---

## Critical Priority

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| B-C1 | Implement custom authentication flow (register/login/logout/session identity) with secure password handling | backend | 2d | done | Merged via PR #1 (`feat/custom-authentication-flow`); tracker was stale |
| B-C2 | Implement authorization schema and policy decision service for (user, resource, action) checks | backend | 2d | done | Merged PR #3; `decide()` + deny-before-allow; `AuthPolicyRule` persisted |
| B-C3 | Enforce exact `401` and `403` behavior across protected APIs | backend | 0.5d | done | Explicit `NotAuthenticated`/`PermissionDenied` in `EnforcedAuthzPermission`; regression tests |

## High Priority

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| B-H1 | Implement user profile update and soft-delete (`is_active=False`) with forced logout | backend | 1d | todo | Soft-deleted users must not be able to login again |
| B-H2 | Build admin-only API for managing roles, permissions, and access rules | backend | 2d | todo | Include grant/revoke flows and permission safeguards |
| B-H3 | Seed DB with demo users, roles, permissions, and bindings for showcase scenarios | backend | 0.5d | todo | Required for functional demonstration |

## Medium Priority

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| B-M1 | Add automated tests for auth and authorization decision matrix | backend | 1d | todo | Cover happy paths and denial edge cases |
| B-M2 | Add `.env.example`, config loading, and startup validation of critical env vars | backend | 0.25d | todo | Prevent runtime surprises and secrets leakage |
| B-M3 | Introduce baseline lint/test commands and CI workflow for validation | infra | 0.5d | todo | Needed for reliable `/validate` and PR checks |
| B-M4 | Add selective AI Annotation docstrings to non-trivial backend functions (auth, policy, validation, API handlers), excluding small/obvious helpers | backend | 0.5d | done | Merged PR #2; docstrings only, no runtime change |

## Low Priority

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| B-L1 | Add structured audit logging for auth and policy management actions | backend | 0.5d | todo | Start with essential events and request correlation ID |
| B-L2 | Add health endpoints (`/health/live`, `/health/ready`) for ops readiness | backend | 0.25d | todo | Useful once service is deployable |

## Features

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| FEAT-1 | Add remote repo check to setup-workflow command | workflow | 0.25d | done | Phase 0: detect remote, offer to create via gh CLI |
| FEAT-2 | Build recruitment-task backend skeleton with Django + DRF + Postgres baseline | backend | 1d | todo | Foundation feature aligned with user priority: backend-first implementation |

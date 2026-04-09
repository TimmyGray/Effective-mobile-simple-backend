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
| B-H1 | Implement user profile update and soft-delete (`is_active=False`) with forced logout | backend | 1d | done | Merged PR #5; PATCH/DELETE `/api/auth/me`, inactive session logout |
| B-H2 | Build admin-only API for managing roles, permissions, and access rules | backend | 2d | done | Merged PR #6; staff + `admin:manage`; CRUD + grants; migration `0007_seed_admin_manage_policy` |
| B-H3 | Seed DB with demo users, roles, permissions, and bindings for showcase scenarios | backend | 0.5d | done | Merged PR #7; migration `0008_seed_demo_showcase_users` + `ARCHITECTURE.md` demo table |

## Medium Priority

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| B-M1 | Add automated tests for auth and authorization decision matrix | backend | 1d | done | Merged PR #8; policy + HTTP matrix tests (`PolicyDecideTests`, `AuthzDecisionMatrixApiTests`) |
| B-M2 | Add `.env.example`, config loading, and startup validation of critical env vars | backend | 0.25d | done | Merged PR #10; `config/env.py` + HSTS parse validation; `config/tests/test_env_validation.py` |
| B-M3 | Add dev toolchain: pin Ruff + pytest/pytest-django + type checking (mypy or pyright), `requirements-dev.txt`; local commands for lint/test/typecheck; GitHub Actions on `pull_request` (opened/synchronize/reopened) so every PR update on any branch runs lint, tests, and typecheck | infra | 1d | done | `requirements-dev.txt`, `pyproject.toml`, `.github/workflows/ci.yml`; `mypy -p config` baseline; accounts gradual typing deferred |
| B-M4 | Add selective AI Annotation docstrings to non-trivial backend functions (auth, policy, validation, API handlers), excluding small/obvious helpers | backend | 0.5d | done | Merged PR #2; docstrings only, no runtime change |

## Low Priority

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| B-L1 | Add structured audit logging for auth and policy management actions | backend | 0.5d | done | Merged PR #11; `accounts.audit` + `CorrelationIdMiddleware` + JSON formatter |
| B-L2 | Add health endpoints (`/health/live`, `/health/ready`) for ops readiness | backend | 0.25d | todo | Useful once service is deployable |

## Features

| ID | Task | Area | Effort | Status | Notes |
|----|------|------|--------|--------|-------|
| FEAT-1 | Add remote repo check to setup-workflow command | workflow | 0.25d | done | Phase 0: detect remote, offer to create via gh CLI |
| FEAT-2 | Build recruitment-task backend skeleton with Django + DRF + Postgres baseline | backend | 1d | todo | Foundation feature aligned with user priority: backend-first implementation |
| FEAT-3 | Improve workflow for manual API checks (curl/httpie): documented steps, CSRF cookie/header, 401 vs 403 probes, optional small script under `docs/` or `scripts/` | workflow | 0.25d | todo | Aligns with auth semantics; complements automated tests |

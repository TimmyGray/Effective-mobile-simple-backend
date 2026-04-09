# Roadmap

## Phase 1: Foundation

- Define backend project skeleton and dependency baseline (Django, DRF, PostgreSQL driver, pytest).
- Implement user model strategy and migration plan.
- Deliver core auth flows: register, login, logout, profile update, soft delete.
- Define and migrate authorization tables (roles, permissions, user-role, role-permission).

## Phase 2: Quality

- Add automated tests for authentication and authorization decision matrix.
- Add input validation hardening and consistent error response format.
- Introduce baseline linting, type checking, and test commands for CI/local validation (see backlog `B-M3`).
- Document a manual API verification workflow (curl/httpie, CSRF) for quick checks (see backlog `FEAT-3`).
- Add readiness/liveness endpoints and basic structured logging.

## Phase 3: Features

- Build admin APIs for role and permission management.
- Seed demo data for minimal demonstrable scenarios.
- Implement mock business resource endpoints guarded by policy checks.

## Phase 4: Polish

- Improve audit logs and operator observability for access changes.
- Refactor authorization service for clarity and extension points.
- Document API contract and data model decisions for reviewer presentation.

## Future

See `docs/PRODUCT_SENSE.md` for prioritized feature list.
See `docs/exec-plans/tech-debt-tracker.md` for detailed backlog.

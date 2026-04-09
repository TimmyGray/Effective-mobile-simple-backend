# Code Conventions

## General

- Keep modules small and cohesive; split files before they become hard to review.
- Prefer explicit, boring code over abstractions.
- Deny access by default when policy lookup is inconclusive.
- Avoid `print`/`console` style debug logging in production paths.
- Raise explicit HTTP errors with actionable messages for clients.

## Backend

- Framework target: Django + DRF.
- Validate all request payloads at serializer/schema boundary.
- Keep business rules in services/domain layer, not in views/controllers.
- Every protected endpoint must call centralized authz evaluation.
- Enforce status codes:
  - `401` unauthenticated.
  - `403` authenticated but forbidden.
- Implement user soft-delete via `is_active=False`; never hard-delete user records by default.
- Use database migrations for all schema changes and commit migration files.
- Prefer transactions around multi-step auth/authz state changes.

## Frontend

Not applicable for current repository scope.

## Git

- Branches: `feat/<kebab>`, `fix/<kebab>`, `chore/<kebab>`
- Commits: descriptive, focused on "why"
- Staging: explicit by name (never `git add .` or `git add -A`)

## Mechanically Enforced Rules

Current status: not configured yet (no linter/type/test toolchain committed yet).

Planned baseline:
1. `ruff` for style and basic static analysis.
2. `pytest` + `pytest-django` for test enforcement.
3. Optional `mypy` for stricter typing once project structure stabilizes.
4. Architecture tests for authz boundaries (policy checks required on protected routes).

## Environment

- Never commit `.env` files.
- Provide a `.env.example` once backend code is scaffolded.
- Configuration must be read from environment variables with safe defaults for local development.

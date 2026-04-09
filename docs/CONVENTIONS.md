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

Baseline (see `requirements-dev.txt`, `pyproject.toml`, `.github/workflows/ci.yml`):

1. **`ruff check .`** — style and basic static analysis (Ruff defaults).
2. **`pytest`** — Django tests under `accounts/` via `pytest-django`.
3. **`mypy -p config`** — typecheck Django settings package; `accounts` is deferred until gradual typing.
4. GitHub Actions runs the same checks on every pull request.

Planned: architecture tests for authz boundaries (policy checks required on protected routes).

## Environment

- Never commit `.env` files.
- Provide a `.env.example` once backend code is scaffolded.
- Configuration must be read from environment variables with safe defaults for local development.

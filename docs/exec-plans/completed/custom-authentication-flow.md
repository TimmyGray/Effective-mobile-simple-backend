# Execution Plan: B-C1 Custom Authentication Flow

## Task Description

Implement a custom authentication flow (register/login/logout/session identity) with secure password handling for the backend recruitment project.

## Acceptance Criteria

- Email-based custom user model is in place.
- API endpoints exist for register, login, logout, and identity lookup.
- Passwords are hashed using Django's password hashing framework.
- Unauthenticated identity requests return `401`.
- Automated tests cover happy path and key auth failures.

## Implementation Phases

1. Bootstrap Django + DRF project baseline (0.25d)
2. Implement custom user model and auth serializers/views (0.75d)
3. Add API routing and tests for auth flow semantics (0.5d)
4. Validate locally and update docs (0.5d)

## Files Created / Modified

- `manage.py`
- `requirements.txt`
- `config/`
- `accounts/`
- `README.md`
- `.gitignore`

## Decision Log

- Chose Django session-based auth for login/logout baseline because it supports immediate identity resolution and keeps auth semantics explicit.
- Chose custom `User` model with `email` as `USERNAME_FIELD` to satisfy custom auth requirement and avoid framework-default username-centric flow.
- Added API tests first for expected `401` behavior and credential validation outcomes.
- Switched to fail-fast secret key configuration and deny-by-default DRF permission defaults after security review.
- Added centralized policy permission checks on protected auth endpoints plus a forbidden-path probe to verify `403` semantics.
- Migrated auth policy allow-list to database-backed rules to keep authorization as durable data with deny-by-default fallback.

## Risks / Open Questions

- Current baseline uses SQLite for local dev; production Postgres wiring remains to be completed in follow-up tasks.
- CSRF and cookie policy hardening for browser clients should be finalized when frontend integration begins.

# Architecture

## System Overview

This project targets a backend recruitment task: implement a custom authentication and authorization platform (not only out-of-the-box framework auth) with clear policy storage, enforcement, and admin management APIs.

Recommended baseline stack:

- Backend: Django + Django REST Framework
- Database: PostgreSQL
- Test stack: pytest + pytest-django

Primary goals:

1. User lifecycle: register, login, logout, profile update, soft delete.
2. Access control engine: explicit resource/action policies with role-based and direct user grants.
3. Admin API: manage roles, permissions, user-role binding, and policy rules.
4. Demo business resources via mock endpoints that validate access decisions.

## Project Structure

```text
.
├── CLAUDE.md
├── ARCHITECTURE.md
├── docs/
│   ├── CONVENTIONS.md
│   ├── SECURITY.md
│   ├── RELIABILITY.md
│   ├── PRODUCT_SENSE.md
│   ├── PLANS.md
│   ├── QUALITY_SCORE.md
│   ├── DESIGN.md
│   ├── design-docs/
│   │   └── core-beliefs.md
│   └── exec-plans/
│       ├── tech-debt-tracker.md
│       └── maintenance-cadence.json
└── .claude/commands/
```

## Backend Architecture

Planned modules:

- `accounts`: registration, login, logout, profile CRUD, soft delete.
- `authn`: credential verification, password hashing, session/token issuance.
- `authz`: policy decision point, permission matrix, role and grant evaluation.
- `admin_access`: privileged APIs to manage roles, resources, actions, and grants.
- `mock_resources`: demo endpoints protected by authz checks.

Planned auth flow:

1. User authenticates with email/password.
2. Server issues credential artifact (session cookie or signed token).
3. Request middleware resolves current user for each request.
4. Authorization layer evaluates `(user, resource, action)` against policy tables.
5. API returns:
   - `401` when user identity cannot be established.
   - `403` when user is authenticated but not authorized.

Planned data model (high level):

- `users`: identity + profile + `is_active`.
- `roles`: named security roles.
- `permissions`: resource/action combinations.
- `role_permissions`: many-to-many role grants.
- `user_roles`: user-to-role assignments.
- Optional direct grants/revocations for exceptional access.

**Runtime evaluation (`accounts.policy.decide`):** explicit `AuthPolicyRule` denies first, then explicit allows, then the **RBAC matrix** — access is granted if the user has a bound role whose `RolePermission` row references an `AccessPermission` with the same `(resource, action)` as the request. If nothing matches, the decision is deny-by-default.

## Operations & health

- **Liveness / readiness:** `GET /health/live` returns `200` when the process serves HTTP; `GET /health/ready` checks the default database via `connection.ensure_connection()` and returns `503` when the DB is unreachable. Implemented as plain Django views in `config.health` (not DRF), so default API authentication does not apply.

## Frontend Architecture

Not applicable for current scope. This repository is currently backend-focused.

## Technology Stack

| Layer | Technology |
| ----- | ---------- |
| Backend | Django + DRF |
| Frontend | N/A |
| Database | PostgreSQL when `DATABASE_URL` or `POSTGRES_HOST`/`PGHOST` is set; otherwise SQLite (`db.sqlite3`) for local dev and optional quick runs |
| Testing | pytest + pytest-django |
| Build | Python packaging + migration workflow |

## Environment Variables

Planned variables:

- `DJANGO_SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL` (or discrete DB host/user/pass/name/port vars)
- `CORS_ALLOWED_ORIGINS` (if cross-origin clients are used)
- `ACCESS_TOKEN_TTL_MINUTES` / `SESSION_TTL_MINUTES`

## Demo showcase accounts (local / recruitment only)

After `python manage.py migrate`, migration `0008_seed_demo_showcase_users` creates fixed accounts for functional demos. **Do not use these credentials in production.**

| Email | Password | Purpose |
| ----- | -------- | --------- |
| `demo.member@example.com` | `DemoShowcase2026!` | Bound to role `member`; `widgets:list` is granted via the RBAC matrix from `0006`. |
| `demo.staff@example.com` | same | `is_staff=True`; satisfies `AuthPolicyRule` allow for `admin:manage` (see `0007`). |
| `demo.plain@example.com` | same | No `UserRole`; authenticated but no matrix grant for `widgets` (deny-by-default for that resource). |

## Security Considerations

Key controls:

- Password hashing with modern algorithm and policy.
- Centralized authorization checks for every protected endpoint.
- Principle of least privilege and deny-by-default policy evaluation.
- Soft-delete account behavior must revoke active sessions/tokens.
- No hardcoded secrets, strict environment-based configuration.
- Structured audit logging for auth and authz changes.

# Effective Mobile Simple Backend

Backend service for a recruitment-style task: custom authentication and authorization with explicit policy evaluation, admin management APIs, structured audit logging, and operational health checks.

## Project Goals

- Build a custom auth/authz layer on top of Django + DRF (not framework defaults only).
- Enforce clear `401` vs `403` semantics on protected APIs.
- Support full user lifecycle: register, login, logout, profile update, soft delete.
- Provide admin APIs to manage roles, permissions, user-role bindings, and policy rules.
- Keep behavior verifiable through automated tests and reproducible manual API probes.

## Tech Stack

- Python 3.12+
- Django
- Django REST Framework
- PostgreSQL (production/CI baseline) with SQLite fallback for local runs
- pytest + pytest-django, Ruff, mypy (config package)

## High-Level Architecture

### Module map

- `config/`
  - Project settings, env validation, DB selection, root routes, health endpoints.
- `accounts/`
  - Authentication endpoints (`register`, `login`, `logout`, `me`, `csrf`).
  - Authorization enforcement (`EnforcedAuthzPermission`, policy engine).
  - Admin RBAC/policy management endpoints.
  - Audit logging and correlation ID middleware.

### Request and authorization flow

1. Request enters Django middleware stack, including `CorrelationIdMiddleware`.
2. DRF authenticates via `SessionAuthentication401`.
3. DRF permissions run `EnforcedAuthzPermission`.
4. Permission delegates to `accounts.policy.decide(user, resource, action)`:
   - explicit deny rules first,
   - explicit allow rules second,
   - RBAC matrix grants third,
   - default deny otherwise.
5. API returns:
   - `401 Unauthorized` if identity is missing/invalid,
   - `403 Forbidden` if identity is valid but policy denies access.

Health endpoints (`/health/live`, `/health/ready`) are plain Django views and bypass DRF auth flow.

## Getting Started

### 1) Prerequisites

- Python 3.12+
- pip
- Optional: PostgreSQL 16+ (if not using SQLite fallback)

### 2) Create virtual environment

### PowerShell (Windows)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Bash (Linux/macOS/Git Bash)

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### 4) Configure environment

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash:

```bash
cp .env.example .env
```

Edit `.env` for your local setup:

- `DJANGO_SECRET_KEY`
- `DEBUG=true` for local dev
- `ALLOWED_HOSTS`
- DB config (`DATABASE_URL` or `POSTGRES_*` / `PG*` vars)
- cookie/HSTS/security flags

### 5) Apply migrations and run

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Environment and database behavior

- If `DATABASE_URL` is set with `postgres://` or `postgresql://`, PostgreSQL is used.
- If `POSTGRES_HOST` or `PGHOST` is set, PostgreSQL is used from discrete vars.
- Otherwise SQLite is used at `db.sqlite3`.

## API Routes

Base prefix: `/api/auth`

### Public routes

| Method | Route | Auth | Description |
|---|---|---|---|
| `GET` | `/api/auth/csrf` | Public | Returns CSRF token for state-changing requests. |
| `POST` | `/api/auth/register` | Public | Registers a new user. |
| `POST` | `/api/auth/login` | Public | Authenticates user and starts a session. |

### Authenticated user routes

| Method | Route | Policy action | Description |
|---|---|---|---|
| `POST` | `/api/auth/logout` | `auth:logout` | Ends current session. |
| `GET` | `/api/auth/me` | `auth:me` | Returns current user profile. |
| `PATCH` | `/api/auth/me` | `auth:profile_update` | Updates own profile and optional password. |
| `DELETE` | `/api/auth/me` | `auth:account_deactivate` | Soft-deletes account (`is_active=false`) and logs out. |
| `GET` | `/api/auth/admin-probe` | `auth:admin_probe` | Probe endpoint for policy/semantics checks. |

### Admin management routes

All require:

- authenticated session,
- staff user,
- policy allow for `admin:manage`.

| Method | Route | Description |
|---|---|---|
| `GET` / `POST` | `/api/auth/admin/roles` | List or create roles. |
| `GET` / `PATCH` / `DELETE` | `/api/auth/admin/roles/{id}` | Read/update/delete role. |
| `GET` / `POST` | `/api/auth/admin/access-permissions` | List or create `(resource, action)` permissions. |
| `GET` / `PATCH` / `DELETE` | `/api/auth/admin/access-permissions/{id}` | Read/update/delete permission. |
| `POST` | `/api/auth/admin/roles/{role_id}/permissions` | Grant permission to role. |
| `DELETE` | `/api/auth/admin/roles/{role_id}/permissions/{permission_id}` | Revoke permission from role. |
| `POST` | `/api/auth/admin/users/{user_id}/roles` | Grant role to user. |
| `DELETE` | `/api/auth/admin/users/{user_id}/roles/{role_id}` | Revoke role from user. |
| `GET` / `POST` | `/api/auth/admin/policy-rules` | List or create policy rules. |
| `GET` / `PATCH` / `DELETE` | `/api/auth/admin/policy-rules/{id}` | Read/update/delete policy rule. |

### Operational routes

| Method | Route | Description |
|---|---|---|
| `GET` | `/health/live` | Liveness probe (process is up). |
| `GET` | `/health/ready` | Readiness probe (DB connectivity check). |
| `GET` | `/admin/` | Django admin UI. |

## Database Entities

Primary entities from `accounts/models.py`:

| Entity | Purpose | Key fields / constraints |
|---|---|---|
| `User` | Custom auth user (`AUTH_USER_MODEL`) | `email` unique; email-based login; soft delete via `is_active`. |
| `Role` | Named security role | `name` unique. |
| `AccessPermission` | Grantable capability | Unique `(resource, action)`. |
| `RolePermission` | RBAC matrix row | Unique `(role, access_permission)`. |
| `UserRole` | User-role binding | Unique `(user, role)`. |
| `AuthPolicyRule` | Explicit allow/deny override | Unique `(resource, action, subject_type, subject_value)`. |

### Entity relationships

- `User` many-to-many `Role` via `UserRole`.
- `Role` many-to-many `AccessPermission` via `RolePermission`.
- `AuthPolicyRule` matches by:
  - `subject_type=any` (all authenticated users),
  - `subject_type=user` + email in `subject_value`,
  - `subject_type=role` + role name in `subject_value`.

### Authorization precedence

1. Explicit deny rule (`AuthPolicyRule.is_allowed = false`)
2. Explicit allow rule (`AuthPolicyRule.is_allowed = true`)
3. RBAC matrix grant (`UserRole` + `RolePermission` + `AccessPermission`)
4. Deny by default

## Demo Seed Accounts

After `python manage.py migrate`, demo users are seeded (for local/recruitment demos only):

| Email | Password | Typical behavior |
|---|---|---|
| `demo.member@example.com` | `DemoShowcase2026!` | Authenticated, member-level matrix grants. |
| `demo.staff@example.com` | `DemoShowcase2026!` | Staff user, can access admin management APIs when policy allows. |
| `demo.plain@example.com` | `DemoShowcase2026!` | Authenticated with minimal/default access. |

Do not use these credentials in production.

## Validation and Quality Commands

Set environment first:

PowerShell:

```powershell
$env:DJANGO_SECRET_KEY="local-dev-not-secret"
$env:DEBUG="true"
```

Bash:

```bash
export DJANGO_SECRET_KEY=local-dev-not-secret
export DEBUG=true
```

Then run:

```bash
ruff check .
mypy -p config
pytest
python manage.py check
```

## Manual API Checks

For CSRF/session flow and `401`/`403` probes:

- `docs/manual-api-checks.md`
- `python scripts/smoke_auth.py`
- `python scripts/probe_auth_semantics.py http://127.0.0.1:8000`

## Project Documentation

- `ARCHITECTURE.md` - system design and policy model
- `docs/SECURITY.md` - security model and controls
- `docs/RELIABILITY.md` - reliability and error handling
- `docs/CONVENTIONS.md` - coding standards
- `docs/QUALITY_SCORE.md` - current quality metrics


# Product Vision & Strategy

## Vision

Build a recruitment-grade backend service that demonstrates strong engineering judgment in custom authentication and authorization design. The product should prove that access control is modeled, persisted, and enforced systematically, with clear 401/403 behavior and admin-governed policy management.

## User Personas

1. **End User** — Registers, logs in, updates profile, and expects account safety and predictable access decisions.
2. **System Administrator** — Manages roles and permissions and needs clear APIs to grant/revoke access safely.
3. **Technical Reviewer (Hiring Team)** — Evaluates architecture quality, correctness of auth boundaries, and code clarity.

## Feature Prioritization

### P0 — Must Have (Blocking Production)
- Registration with full profile fields, password confirmation, and validation.
- Login/logout with persistent user identification across requests.
- Soft-delete account flow (`is_active=False`) with forced logout and blocked future login.
- Authorization DB schema for resources/actions/roles/user-role bindings.
- Access enforcement with strict `401`/`403` semantics.
- Admin-only API to manage access rules.

### P1 — Should Have (High Impact)
- Seeded test data for roles/permissions and demo users.
- Mock protected business resource endpoints for access control demonstration.
- Basic audit logging for auth/authz events.
- Automated tests for critical auth and access flows.

### P2 — Nice to Have (Polish)
- API documentation for auth/authz policy model.
- Improved operational metrics and dashboards.
- Fine-grained direct grants/denials in addition to role grants.

## Design Principles

1. Simple first — no features users haven't asked for
2. Access control must be explicit, testable, and deny-by-default.
3. Security semantics (`401` vs `403`) must be consistent across all endpoints.
4. Recruiter readability matters: architecture and API behavior should be obvious from code and docs.

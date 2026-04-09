# Security Model

## Current Security Model

Target model for this repository:
- Authentication and authorization are first-class domain modules.
- Authentication is custom-designed (credential validation + server-issued identity artifact).
- Authorization is policy-driven and persisted in DB, not hardcoded in route handlers.
- Access checks are evaluated for each protected request using `(user, resource, action)`.
- User account deletion is soft-delete (`is_active=False`), with immediate logout/session invalidation.

## Threat Model

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Credential stuffing / brute force login | High | Rate limiting + lockout/backoff policy |
| Broken access control | Critical | Centralized authz checks and deny-by-default |
| Privilege escalation via role API | Critical | Admin-only endpoints + audit logs + tests |
| Session/token replay after soft delete | High | Revoke active sessions/tokens on deactivation |
| Secret leakage in repository | Critical | Env vars only + secret scanning in CI |
| Input validation gaps on auth APIs | High | Serializer/schema validation for all boundaries |
| Overly verbose auth errors | Medium | Return safe client errors, keep internals in logs |

## Security Checklist (for Code Reviews)

- [ ] No hardcoded secrets, API keys, or credentials
- [ ] All user input is validated at the boundary (DTOs, schemas)
- [ ] Passwords are hashed and never logged or returned
- [ ] File paths are validated (no path traversal)
- [ ] Rate limiting on sensitive endpoints
- [ ] CORS properly configured
- [ ] Error messages don't leak internal details
- [ ] Dependencies checked for known vulnerabilities
- [ ] Authenticated-not-authorized requests return `403`
- [ ] Unauthenticated requests return `401`
- [ ] Soft-delete users cannot authenticate anymore

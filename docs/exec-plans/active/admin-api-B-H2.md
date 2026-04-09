# B-H2: Admin-only API (roles, permissions, policy rules)

## Acceptance criteria

- Staff/superusers can CRUD named roles, access permissions (resource+action), role↔permission grants, user↔role grants, and `AuthPolicyRule` rows.
- Non-staff authenticated users get 403; unauthenticated get 401.
- Policy `admin:manage` is required (seeded for `staff` and `superuser` role keys).
- Grant/revoke endpoints are idempotent where sensible; safeguards on destructive deletes.

## Implementation notes

- `policy._user_roles()` includes DB `Role.name` from `UserRole` plus legacy `staff`/`superuser` flags.
- Admin views use `EnforcedAuthzPermission` + `IsStaffUser`.

## Files

- `accounts/models.py`, migration `0005_*`
- `accounts/policy.py`, `accounts/permissions.py`
- `accounts/admin_serializers.py`, `accounts/admin_views.py`
- `accounts/urls.py`, `accounts/tests.py`

## Decision log

- Single policy action `admin`/`manage` for all admin endpoints to keep seeds simple.

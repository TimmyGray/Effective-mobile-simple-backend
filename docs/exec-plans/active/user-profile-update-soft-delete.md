# Execution Plan: B-H1 User Profile Update & Soft Delete

## Task Description

Implement user profile update and soft-delete (`is_active=False`) with forced logout. Soft-deleted users must not be able to log in again.

## Acceptance Criteria

- Authenticated users can update profile (email, optional password change with current password, optional name fields).
- Soft delete sets `is_active=False`, clears session (forced logout).
- Login remains rejected for inactive users (existing).
- Stale sessions for deactivated accounts are rejected with `401` and session cleared.
- Policy rules exist for `auth:profile_update` and `auth:account_deactivate`.
- Tests cover happy paths and key failures.

## Files to Modify

- `accounts/authentication.py` — inactive user session rejection
- `accounts/serializers.py` — profile update serializer
- `accounts/views.py` — PATCH/DELETE on `MeView`, `policy_action` property
- `accounts/urls.py` — unchanged paths (`/me` supports new methods)
- `accounts/migrations/0004_*.py` — seed policy rules
- `accounts/tests.py` — API tests

## Decision Log

- PATCH/DELETE on `/api/auth/me` with dynamic `policy_action` from HTTP method.
- `SessionAuthentication401` extended to flush session when user is inactive (forced logout for stale sessions).

## Risks

- Property-based `policy_action` must remain compatible with `EnforcedAuthzPermission` (view instance has `request`).

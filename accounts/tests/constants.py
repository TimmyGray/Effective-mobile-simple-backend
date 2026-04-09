"""
Shared DRF settings fragments for API tests.

AI Annotation:
- Purpose: Single source for `REST_FRAMEWORK` overrides used across API test modules.
- Inputs: DRF setting keys compatible with `django.test.override_settings`.
- Side effects: None at import time; applied only when tests use `@override_settings`.

ScopedRateThrottle reads DRF settings cached at import time; tests that patch
register/login throttles combine this dict with @override_settings.
"""

REST_FRAMEWORK_NO_THROTTLE: dict[str, object] = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.SessionAuthentication401",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "accounts.permissions.EnforcedAuthzPermission",
    ],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {},
}

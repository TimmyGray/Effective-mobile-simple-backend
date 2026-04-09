"""
Centralized environment validation for Django settings.

AI Annotation:
- Purpose: Fail fast on missing or unsafe configuration before the app serves traffic.
- Inputs: Expects `load_dotenv` to have run so `os.environ` reflects `.env` when present.
- Outputs: Raises `ImproperlyConfigured` on violation; returns None on success.
- Failure modes: Empty secrets, production misconfiguration, weak placeholder keys.
- Security notes: Stricter checks apply when `DEBUG` is false (production-like runs).
"""

from __future__ import annotations

import os
from typing import Final

from django.core.exceptions import ImproperlyConfigured

# Exact matches only — avoids accidental substring false positives.
_WEAK_SECRET_KEYS: Final[frozenset[str]] = frozenset(
    {
        "replace-with-long-random-secret",
        "change-me",
        "local-dev-not-secret",
        "ci-django-secret-key-not-for-production",
        "secret",
        "django-insecure-please-change",
    }
)

_MIN_SECRET_LEN_NON_DEBUG: Final[int] = 50


def validate_runtime_environment() -> None:
    """
    AI Annotation:
    - Purpose: Validate critical env vars after dotenv load; complement `config.settings` reads.
    - Side effects: None (read-only inspection of `os.environ`).
    - Security notes: Deny weak or short `DJANGO_SECRET_KEY` when not in DEBUG mode.
    """
    secret = os.getenv("DJANGO_SECRET_KEY", "").strip()
    if not secret:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set to a non-empty value")

    debug = os.getenv("DEBUG", "false").lower() == "true"
    allowed_hosts = [h for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

    if not debug:
        if not allowed_hosts:
            raise ImproperlyConfigured(
                "ALLOWED_HOSTS must list at least one host when DEBUG is false"
            )
        if secret in _WEAK_SECRET_KEYS:
            raise ImproperlyConfigured(
                "DJANGO_SECRET_KEY matches a known placeholder or dev-only value; "
                "set a unique secret for non-DEBUG deployments"
            )
        if secret.lower().startswith("django-insecure-"):
            raise ImproperlyConfigured(
                "DJANGO_SECRET_KEY must not use a django-insecure-* value when DEBUG is false"
            )
        if len(secret) < _MIN_SECRET_LEN_NON_DEBUG:
            raise ImproperlyConfigured(
                f"DJANGO_SECRET_KEY must be at least {_MIN_SECRET_LEN_NON_DEBUG} characters "
                "when DEBUG is false"
            )

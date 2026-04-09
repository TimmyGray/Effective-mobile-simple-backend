"""Tests for `config.env.validate_runtime_environment`."""

from __future__ import annotations

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.env import validate_runtime_environment

_DEV_SECRET = "x" * 49  # below production minimum; allowed when DEBUG=true
_PROD_SECRET = "p" * 50  # meets length requirement for DEBUG=false


def _minimal_good_env() -> dict[str, str]:
    return {
        "DJANGO_SECRET_KEY": _PROD_SECRET,
        "DEBUG": "false",
        "ALLOWED_HOSTS": "example.com",
    }


def test_empty_secret_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.setenv("DEBUG", "true")
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        validate_runtime_environment()


@pytest.mark.parametrize(
    "debug",
    ["true", "True", "TRUE"],
)
def test_debug_mode_allows_short_secret(monkeypatch: pytest.MonkeyPatch, debug: str) -> None:
    monkeypatch.setenv("DJANGO_SECRET_KEY", _DEV_SECRET)
    monkeypatch.setenv("DEBUG", debug)
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    validate_runtime_environment()


def test_non_debug_requires_allowed_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _minimal_good_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("ALLOWED_HOSTS", "")
    with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS"):
        validate_runtime_environment()


def test_non_debug_requires_long_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _minimal_good_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 40)
    with pytest.raises(ImproperlyConfigured, match="at least"):
        validate_runtime_environment()


def test_non_debug_rejects_placeholder_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _minimal_good_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "replace-with-long-random-secret")
    with pytest.raises(ImproperlyConfigured, match="placeholder"):
        validate_runtime_environment()


def test_non_debug_rejects_django_insecure_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _minimal_good_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "django-insecure-" + "a" * 40)
    with pytest.raises(ImproperlyConfigured, match="django-insecure"):
        validate_runtime_environment()


def test_non_debug_accepts_strong_secret_and_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _minimal_good_env().items():
        monkeypatch.setenv(key, value)
    validate_runtime_environment()


def test_strips_whitespace_on_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Whitespace-only after strip should fail as empty."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "   ")
    monkeypatch.setenv("DEBUG", "true")
    with pytest.raises(ImproperlyConfigured, match="non-empty"):
        validate_runtime_environment()


def test_ci_style_secret_allowed_in_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """CI uses a known weak string with DEBUG=true; validation must allow it."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "ci-django-secret-key-not-for-production")
    monkeypatch.setenv("DEBUG", "true")
    validate_runtime_environment()

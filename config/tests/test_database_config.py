"""Tests for `config.database.build_databases`."""

from __future__ import annotations

from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.database import build_databases


def test_default_sqlite_when_no_postgres_signals(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("PGHOST", raising=False)
    base = tmp_path / "proj"
    base.mkdir()
    dbs = build_databases(base)
    assert dbs["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert dbs["default"]["NAME"] == base / "db.sqlite3"


def test_database_url_postgresql(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:secret@db.example:5432/myapp?sslmode=require",
    )
    dbs = build_databases(tmp_path)
    assert dbs["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert dbs["default"]["NAME"] == "myapp"
    assert dbs["default"]["USER"] == "user"
    assert dbs["default"]["PASSWORD"] == "secret"
    assert dbs["default"]["HOST"] == "db.example"
    assert dbs["default"]["PORT"] == "5432"
    assert dbs["default"]["OPTIONS"]["sslmode"] == "require"


def test_database_url_postgres_scheme_alias(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h:5432/db")
    dbs = build_databases(tmp_path)
    assert dbs["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert dbs["default"]["NAME"] == "db"


def test_database_url_rejects_non_postgres(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", "mysql://u:p@h/db")
    with pytest.raises(ImproperlyConfigured, match="postgres"):
        build_databases(tmp_path)


def test_postgres_discrete_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "app")
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")
    dbs = build_databases(tmp_path)
    assert dbs["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert dbs["default"]["HOST"] == "localhost"
    assert dbs["default"]["NAME"] == "app"
    assert dbs["default"]["USER"] == "u"
    assert dbs["default"]["PASSWORD"] == "p"


def test_database_url_takes_precedence_over_postgres_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "should-not-use")
    monkeypatch.setenv("DATABASE_URL", "postgresql://a:b@c:5432/fromurl")
    dbs = build_databases(tmp_path)
    assert dbs["default"]["HOST"] == "c"
    assert dbs["default"]["NAME"] == "fromurl"

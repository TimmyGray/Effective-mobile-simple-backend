"""
Database configuration: SQLite by default, PostgreSQL for recruitment-task baseline.

AI Annotation:
- Purpose: Centralize DATABASES construction from env (DATABASE_URL or discrete PG vars).
- Inputs: `BASE_DIR` for SQLite path; `os.environ` for connection selection.
- Outputs: A Django `DATABASES`-compatible dict with a single `default` entry.
- Failure modes: `ImproperlyConfigured` when `DATABASE_URL` uses a non-Postgres scheme.
- Security notes: Passwords come from env only; never logged here.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured


def build_databases(base_dir: Path) -> dict[str, dict[str, Any]]:
    """
    AI Annotation:
    - Purpose: Pick SQLite (local/CI default) vs PostgreSQL when explicitly configured.
    - Side effects: None (reads environment only).
    """
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return _databases_from_url(database_url)
    if _postgres_env_configured():
        return _databases_from_postgres_env()
    return _sqlite_databases(base_dir)


def _sqlite_databases(base_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": base_dir / "db.sqlite3",
        }
    }


def _postgres_env_configured() -> bool:
    """True when discrete libpq-style host is set (avoids flipping engines on stray PG* vars)."""
    return bool((os.getenv("POSTGRES_HOST") or os.getenv("PGHOST") or "").strip())


def _databases_from_postgres_env() -> dict[str, dict[str, Any]]:
    """
    AI Annotation:
    - Purpose: Support discrete vars for Docker/K8s without requiring a single URL string.
    - Inputs: POSTGRES_* preferred; PG* accepted as fallback (libpq-style names).
    """
    host = (os.getenv("POSTGRES_HOST") or os.getenv("PGHOST") or "localhost").strip()
    port = (os.getenv("POSTGRES_PORT") or os.getenv("PGPORT") or "5432").strip()
    name = (os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE") or "postgres").strip()
    user = (os.getenv("POSTGRES_USER") or os.getenv("PGUSER") or "postgres").strip()
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("PGPASSWORD") or ""
    options: dict[str, Any] = {}
    sslmode = os.getenv("POSTGRES_SSLMODE", "").strip()
    if sslmode:
        options["sslmode"] = sslmode
    cfg: dict[str, Any] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
    }
    if options:
        cfg["OPTIONS"] = options
    return {"default": cfg}


def _databases_from_url(url: str) -> dict[str, dict[str, Any]]:
    """
    AI Annotation:
    - Purpose: Parse `DATABASE_URL` for Postgres deployments (Heroku-style, CI, Docker).
    - Failure modes: Rejects non-postgres schemes so misconfiguration fails fast.
    """
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("postgres", "postgresql"):
        raise ImproperlyConfigured(
            f"DATABASE_URL must use postgres or postgresql scheme, not {scheme!r}"
        )

    path = unquote(parsed.path or "")
    if path.startswith("/"):
        path = path[1:]
    name = path or "postgres"
    user = unquote(parsed.username) if parsed.username else "postgres"
    password = unquote(parsed.password) if parsed.password else ""
    host = parsed.hostname or ""
    port = str(parsed.port) if parsed.port else "5432"

    options = _options_from_query(parsed.query)

    cfg: dict[str, Any] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "PORT": port,
    }
    if options:
        cfg["OPTIONS"] = options
    return {"default": cfg}


def _options_from_query(query: str) -> dict[str, str]:
    if not query:
        return {}
    parsed = parse_qs(query, keep_blank_values=True)
    return {key: values[0] for key, values in parsed.items() if values}

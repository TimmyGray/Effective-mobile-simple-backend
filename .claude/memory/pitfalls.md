# Pitfalls (avoid these)

Phase 9b-style entries: use **category** tags so `/retrospective` can count recurrences and promote at 3+.

## Categories (tag each entry)

- `ENV` — local/network/tooling (PyPI, DB, OS paths)
- `TEST` — wrong command, missing env vars, wrong test selection
- `AUTHZ` — policy/401/403 semantics drift
- `SCOPE` — PR too large or mixed concerns
- `DOCS` — tracker/QUALITY stale vs reality

## Log

<!-- Newest first -->

- **2026-04-09** | `TEST` | Running full-repo `pytest` from a template that includes `_bmad` tests can fail on Windows path expectations; this repo’s canonical command is `pytest` with `testpaths = accounts` (see `pyproject.toml`). Remediation: use project `pytest` / `manage.py test accounts`.

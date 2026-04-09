# Access Boundaries for Backend Agent

## Read Access

- Repository-wide read access for context and integration safety.
- Priority docs: `ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/SECURITY.md`, `docs/RELIABILITY.md`.

## Write Access

- Backend source directories when created (for example: `backend/`, `src/`, Django apps).
- Backend configuration files (`manage.py`, `requirements*.txt`, `pyproject.toml`, env examples).
- Backend tests and migration files.

## Deny Zones

- `.claude/agents/*` outside this agent's folder unless explicitly requested.
- Unrelated design/roadmap docs unless task explicitly includes documentation updates.
- Never use `git add .` or `git add -A`.

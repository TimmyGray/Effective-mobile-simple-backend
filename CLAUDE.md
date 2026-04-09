# CLAUDE.md

This is the entrypoint for Claude Code in this repository. Keep it short and link deeper docs.

## Quick Reference

| What | Where |
| ---- | ----- |
| System architecture | `ARCHITECTURE.md` |
| Coding standards | `docs/CONVENTIONS.md` |
| Security model | `docs/SECURITY.md` |
| Reliability and errors | `docs/RELIABILITY.md` |
| Product scope | `docs/PRODUCT_SENSE.md` |
| Delivery roadmap | `docs/PLANS.md` |
| Baseline quality metrics | `docs/QUALITY_SCORE.md` |
| Engineering principles | `docs/design-docs/core-beliefs.md` |
| Task backlog | `docs/exec-plans/tech-debt-tracker.md` |
| Lint/test promotions log | `docs/exec-plans/promoted-rules-log.md` |
| Workflow mechanics | `docs/WORKFLOW.md` |

## Commands (Quick)

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
python manage.py runserver
```

**Validate (lint, typecheck, tests, Django check)** — after installing dev deps, set `DJANGO_SECRET_KEY` and `DEBUG=true`, then:

```bash
ruff check .
mypy -p config
pytest
python manage.py check
```

## Workflow Commands

`/setup-workflow`, `/add-feature`, `/develop-feature`, `/validate`, `/review-pr`, `/sweep`, `/audit-service`, `/doc-garden`, `/retrospective`, `/update-roadmap`

## Non-Negotiable Rules

- Stage files explicitly by path; never use `git add .` or `git add -A`.
- Build a custom auth/authz system; do not rely only on framework defaults.
- Keep authorization policy server-side and deny by default.
- Return `401` for unauthenticated access and `403` for authenticated but forbidden access.
- Use soft delete for users (`is_active=False`) and force logout on deactivation.
- No secrets in git; use environment variables.

See `docs/CONVENTIONS.md` and `docs/WORKFLOW.md` for full details.

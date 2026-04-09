# Quality Metrics

<!-- Updated automatically by /audit-service and /sweep -->

Baseline captured during `/setup-workflow` on 2026-04-09.

## Test Summary

| Suite | Files | Tests | Pass Rate |
|-------|-------|-------|-----------|
| Backend (`pytest`, `accounts/`, `config/tests`) | 12 | 67 | 100% |
| Frontend | N/A | N/A | N/A |
| **Total** | 12 | 67 | 100% |

## Lint / Type / Build

| Check | Errors | Warnings |
|-------|--------|----------|
| Backend Lint (`ruff check .`) | 0 | 0 |
| Frontend Lint | N/A | N/A |
| Backend Types (`mypy -p config`) | 0 | 0 |
| Frontend Types | N/A | N/A |
| Backend Build (`python manage.py check`) | 0 | 0 |
| Frontend Build | N/A | N/A |

## Dependencies

| Scope | Packages | Outdated | Vulnerabilities |
|-------|----------|----------|-----------------|
| Backend (`requirements.txt` + `requirements-dev.txt`) | 11 declared (4 runtime + 7 dev pins) | See `pip list --outdated` locally | CI enforces `pip>=26.0.1` + `pip-audit` on installed env |
| Frontend | N/A | N/A | N/A |

## Tech Debt Status

| Priority | Todo | Done |
|----------|------|------|
| Critical | 0 | 3 |
| High | 0 | 3 |
| Medium | 0 | 4 |
| Low | 0 | 4 |
| Features | 0 | 3 |

## Sweep History

<!-- Append entries here after each /sweep or /audit-service run -->
- 2026-04-09: Initial baseline established. Validation commands and dependency audits are not yet configured because application manifests are not present in repository root.
- 2026-04-09 (Phase 12 sweep): Cadence threshold met for sweep; removed unused `get_user_model` import in `accounts/admin_serializers.py`; `manage.py test accounts` — 31 passed. Audit and retrospective not due (counters 3/5 and 3/10).
- 2026-04-09 (`/develop-feature` Phase 12 audit): `manage.py test accounts` — 40 passed; CLAUDE.md quick-reference paths verified; lint/types still not configured (B-M3).
- 2026-04-09 (post-merge sweep, PR #8 on `main`): `manage.py test accounts` — 40 passed; `accounts/tests.py` ~691 lines (split into submodules deferred); no mechanical fixes applied.
- 2026-04-09 (B-M3): `requirements-dev.txt` + `pyproject.toml` + GitHub Actions; `ruff check .`, `mypy -p config`, `pytest`, `manage.py check` — all clean with `DJANGO_SECRET_KEY` + `DEBUG=true`.
- 2026-04-09 (post-merge sweep, B-L1 / PR #11 on `main`): `pytest` — 58 passed; `accounts/tests.py` ~886 lines (split deferred per sweep rules); maintenance cadence sweep counter reset; no code changes.
- 2026-04-09 (post-merge B-L2 PR #12 + Phase 12 audit cadence): `pytest` — 61 passed; `ruff` / `mypy -p config` / `manage.py check` clean; `ARCHITECTURE.md` updated for health endpoints; tech-debt tracker B-L2 marked done; maintenance `features_since_last_audit` threshold met and reset.
- 2026-04-09 (post-merge FEAT-3 / PR #14 on `main`): `pytest` — 67 passed; `ruff` / `mypy -p config` clean; `accounts/tests.py` ~785 lines (split deferred); tech-debt tracker FEAT-3 marked done; maintenance sweep cadence threshold met and counter reset.
- 2026-04-09 (B-L3 + B-L4): `accounts/tests/` package with 9 `test_*.py` modules + `constants.py`; CI `pip>=26.0.1` + `pip-audit` step; `pip-audit==2.10.0` dev pin; tracker B-L3/B-L4 done; 12 pytest files total (`accounts` + `config/tests`).

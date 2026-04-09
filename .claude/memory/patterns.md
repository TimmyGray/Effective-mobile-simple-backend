# Patterns (repeat these)

Structured memory for `/retrospective` and agents. Update after notable wins.

## 2026-04-09 retrospective (PRs #1–#9)

- **Policy + HTTP matrix tests**: `PolicyDecideTests` and `AuthzDecisionMatrixApiTests` lock `decide()` semantics and stable `reason` codes alongside 401/403 behavior — good template for new auth surfaces.
- **CI gate before merge**: B-M3 (`ruff`, `mypy -p config`, `pytest`, `manage.py check` on PR sync) prevents drift once dev deps are installed locally.
- **Incremental backlog mapping**: Tech-debt tracker IDs (B-C*, B-H*, B-M*) referenced in PR titles keeps traceability without heavy process.

## 2026-04-10 retrospective (PRs #7–#16)

- **Ops-shaped features ship with tests**: health endpoints (`config/tests/test_health.py`) and env validation (`config/tests/test_env_validation.py`) set a pattern — probe behavior, stable status codes, and JSON bodies in tests.
- **Postgres baseline in CI**: FEAT-2 style changes (service container + `DATABASE_URL`) catch driver/config regressions early; keep SQLite fallback documented for local-only dev.
- **Split tests before they become merge risk**: B-L3 moved domain-grouped modules under `accounts/tests/`; prefer adding new cases to the smallest existing `test_*.py` by domain rather than growing one file.
- **Manual verification as code**: FEAT-3 (`docs/manual-api-checks.md` + `scripts/probe_auth_semantics.py`) complements automated matrix tests for session/CSRF flows agents cannot easily simulate in pytest alone.
- **Supply-chain hygiene**: pip minimum + `pip-audit` in CI (B-L4) addresses recurring audit noise about toolchain CVEs without app code churn.

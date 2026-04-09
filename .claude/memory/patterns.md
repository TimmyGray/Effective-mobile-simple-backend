# Patterns (repeat these)

Structured memory for `/retrospective` and agents. Update after notable wins.

## 2026-04-09 retrospective (PRs #1–#9)

- **Policy + HTTP matrix tests**: `PolicyDecideTests` and `AuthzDecisionMatrixApiTests` lock `decide()` semantics and stable `reason` codes alongside 401/403 behavior — good template for new auth surfaces.
- **CI gate before merge**: B-M3 (`ruff`, `mypy -p config`, `pytest`, `manage.py check` on PR sync) prevents drift once dev deps are installed locally.
- **Incremental backlog mapping**: Tech-debt tracker IDs (B-C*, B-H*, B-M*) referenced in PR titles keeps traceability without heavy process.

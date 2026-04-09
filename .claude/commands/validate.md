# Validation Suite

Run all validation checks and report results.

## Checks

Run each check and record pass/fail. Use this backend-first command order:

1. **Lint**: `ruff check .` (requires `pip install -r requirements-dev.txt`)
2. **Typecheck**: `mypy -p config` (Django project package; requires dev deps; set `DJANGO_SECRET_KEY` and `DEBUG=true`)
3. **Tests**: `pytest` (collects `accounts` tests only; set `DJANGO_SECRET_KEY` and `DEBUG=true`)
4. **Build/Runtime sanity**: `python manage.py check` (set `DJANGO_SECRET_KEY` and `DEBUG=true`)

If dev dependencies are missing, mark the affected check as `NOT CONFIGURED` rather than failing silently.

## Staged Completeness Check

When run before a commit (i.e., there are staged or unstaged changes):

1. Run `git status --short`
2. For each `??` (untracked) file:
   - Check if any staged source file imports it
   - If found, report as `UNSTAGED DEPENDENCY: <file>`
3. For each ` M` (unstaged modified) file:
   - Check if this file was modified as part of the current work
   - If found, report as `UNSTAGED MODIFICATION: <file>`
4. If no issues: `Staged Completeness: PASS`

This prevents the most common CI failure: files that exist on disk but aren't committed.

## Output

Present results as a summary table:

| Check | Status | Details |
|-------|--------|---------|
| Lint | PASS/FAIL | error count or "clean" |
| Typecheck | PASS/FAIL | error count or "clean" |
| Tests | PASS/FAIL | X passed, Y failed |
| Build | PASS/FAIL | |
| Staged Completeness | PASS/WARN | unstaged dependency count or "clean" |

If any check fails, provide the first few lines of error output for quick diagnosis.

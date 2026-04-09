# Documentation Gardening

Scan for stale, broken, or inconsistent documentation and open fix-up PRs automatically.

## Process

### 1. Structural Integrity Check

Verify all files referenced in `CLAUDE.md` Quick Reference table exist. For each missing file, report: `BROKEN REFERENCE: <file> referenced in CLAUDE.md but does not exist`

### 2. Architecture Doc vs Reality

1. Read `ARCHITECTURE.md` — extract the module/component list
2. List actual source directories and modules on disk
3. Compare: report modules in docs but not on disk, or on disk but not in docs
4. Check that API endpoints listed in ARCHITECTURE.md actually exist in the codebase

### 3. Quality Score Staleness

1. Read `docs/QUALITY_SCORE.md`
2. Run current validation checks and compare metrics
3. If any metric differs, update the doc

### 4. Tech Debt Tracker Consistency

1. Read `docs/exec-plans/tech-debt-tracker.md`
2. For tasks marked `done`: verify the fix actually exists in the codebase
3. For tasks marked `todo`: check if they were already addressed

### 5. Cross-Link Validation

For every markdown file in `docs/`:
- Extract all relative links
- Verify each link target exists
- Report broken links

### 6. Core Beliefs vs Practice

1. Read `docs/design-docs/core-beliefs.md`
2. For each belief, spot-check one example in the codebase
3. Report any violations found

### 7. Report & Fix

If any issues found:
1. Fix all documentation issues directly
2. Create branch: `git checkout -b chore/doc-garden-$(date +%Y%m%d)`
3. Stage fixed files explicitly by name
4. Commit and create PR with the report as description

If no issues: `Documentation is healthy. No fixes needed.`

## Cadence
- After every `/audit-service`
- Before any major release
- When ARCHITECTURE.md or CLAUDE.md is modified
- On demand when documentation seems stale

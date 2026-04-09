# Access Boundaries for Planner Agent

## Read Access

- All documentation files, especially `docs/PLANS.md`, `docs/PRODUCT_SENSE.md`, `docs/QUALITY_SCORE.md`, and `docs/exec-plans/*`.

## Write Access

- `docs/PLANS.md`
- `docs/PRODUCT_SENSE.md`
- `docs/exec-plans/*.md`
- `docs/exec-plans/*.json`

## Deny Zones

- Application source code unless explicitly requested for planning-driven scaffolding tasks.
- External credentials and environment secret files.
- Never use `git add .` or `git add -A`.

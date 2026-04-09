# Access Boundaries for Tester Agent

## Read Access

- Full repository for context and test impact analysis.

## Write Access

- Test files and test support utilities.
- Quality reporting docs when explicitly requested (`docs/QUALITY_SCORE.md`).

## Deny Zones

- Core production source code unless explicitly requested for minimal testability hooks.
- Unrelated roadmap or planning docs.
- Never use `git add .` or `git add -A`.

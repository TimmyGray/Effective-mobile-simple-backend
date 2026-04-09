# Access Boundaries for Reviewer Agent

## Read Access

- Full repository, including all source, tests, docs, and command specs.

## Write Access

- None by default. Reviewer is advisory-only.

## Deny Zones

- Do not modify source code or docs unless explicitly requested as a follow-up fix task.
- Never use `git add .` or `git add -A`.

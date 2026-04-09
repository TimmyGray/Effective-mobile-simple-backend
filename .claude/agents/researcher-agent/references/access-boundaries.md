# Access Boundaries for Researcher Agent

## Read Access

- Full repository read access for roadmap and architecture context.

## Write Access

- Research outputs and planning docs when requested:
  - `docs/*.md`
  - `docs/exec-plans/*.md`
  - `docs/references/*` (if present)

## Deny Zones

- Production source code edits unless explicitly requested.
- Any secret-containing files or environment files.
- Never use `git add .` or `git add -A`.

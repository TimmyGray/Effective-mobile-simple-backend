# Promoted Rules Log

Mechanical enforcement promoted from repeated review or sweep findings (see `/retrospective`).

## Promoted Rules Log

| Date | Pattern | Promoted To | Rule/Test Name |
|------|---------|-------------|----------------|
| 2026-04-09 | *(none this cycle — no 3+ recurring review/sweep issue with evidence)* | — | — |
| 2026-04-10 | *(none — no 3+ recurring review/sweep issue with evidence)* | — | — |

### Notes

- **2026-04-09**: Analyzed merged PRs #1–#9 (2026-04-09). No GitHub review thread data; sweep history shows one-off unused import (Ruff F401 already covers). B-M3 added CI; no additional lint rule required yet per “3+ same-type finding” bar.
- **2026-04-10**: Analyzed merged PRs #7–#16 (merged 2026-04-09 UTC). `gh pr view` returned empty `comments` and `reviews` for each; no repeated human review threads to mine. Sweep history + bodies show one-off themes (monolithic tests → B-L3 resolved; pip CVE → B-L4). Phase 9b `pitfalls.md`: one `TEST` entry (not ≥3). Bar for new lint/structural promotion not met.

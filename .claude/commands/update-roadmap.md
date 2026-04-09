# Strategic Roadmap Update

Research industry trends, propose new features interactively, and update all roadmap documents.

> Inspired by: "Humans steer, agents execute" — The agent researches the landscape, but the human decides which direction to go.

## Process

### 1. Pre-Flight Check

Verify clean working tree on `main`:
```bash
git status --porcelain
git branch --show-current
```

If the working tree is dirty or not on `main`, stop and ask the user to resolve before continuing.

### 2. Load Current State

Read these files to understand the current roadmap:
- `docs/PRODUCT_SENSE.md` — product vision, personas, prioritized features
- `docs/PLANS.md` — phased roadmap, milestones
- `docs/exec-plans/tech-debt-tracker.md` — task backlog with FEAT-* IDs and statuses
- `docs/design-docs/core-beliefs.md` — engineering principles (for alignment checks)

Extract and note:
- **Completed features** — tasks marked `done` in the tracker
- **In-progress features** — tasks marked `in-progress`
- **Planned but not started** — tasks still `todo`
- **Highest FEAT-* ID** — for auto-incrementing new IDs later
- **Stale items** — features listed as planned in PRODUCT_SENSE.md or PLANS.md but already completed in the tracker

### 3. Present State Summary

Show the user a concise summary:
```
## Current Roadmap State

### Completed (X features)
- FEAT-XX: <description>
- ...

### In Progress (X features)
- FEAT-XX: <description>
- ...

### Planned / Not Started (X features)
- FEAT-XX: <description>
- ...

### Stale Items (needs cleanup)
- <feature name> — listed as planned but already done
- ...

### Highest FEAT ID: FEAT-XX
```

Ask the user to confirm this summary is accurate before proceeding.

### 4. Research Industry Trends

Perform **at least 4** web searches to understand the current landscape. Tailor searches to the project's domain (detected from PRODUCT_SENSE.md and ARCHITECTURE.md).

Required search categories:

1. **Competitor landscape** — search for recent features in competing projects or products in the same space. Identify direct competitors from the product vision doc.
2. **Ecosystem trends** — search for emerging patterns, tools, libraries, and architectural shifts relevant to the project's tech stack and domain.
3. **User expectations** — search for most-requested features in the project's domain, community discussions (Reddit, HN, GitHub issues on comparable projects).
4. **Focused search** — if `$ARGUMENTS` is provided, run an additional targeted search on that topic.

For each search, extract and note:
- Key features competitors have shipped recently
- Trends gaining momentum
- Gaps that represent opportunities

### 5. Synthesize & Propose

Based on the research, propose **3–5 new features** for the roadmap. For each feature:

| Field | Description |
|-------|-------------|
| **Name** | Short, descriptive feature name |
| **Description** | 2–3 sentence summary of what it does and why |
| **Rationale** | Cite specific research findings (competitor X shipped this, trend Y is growing) |
| **Personas Served** | Which user personas benefit (reference PRODUCT_SENSE.md personas) |
| **Principle Check** | Which core beliefs from `core-beliefs.md` this aligns with |
| **Area** | `backend`, `frontend`, or `full-stack` |
| **Effort** | `S` / `M` / `L` / `XL` — calibrate against completed tasks of similar scope |
| **Priority** | `P0` (must-have) / `P1` (should-have) / `P2` (nice-to-have) |

Present the proposals in a clear table format.

### 6. Interactive Review

Present all candidates to the user and ask them to:
- **Select** which features to add to the roadmap
- **Modify** any details (rename, reprioritize, change effort)
- **Add** any features the user wants that weren't proposed

Use a single batch question with `AskUserQuestion`. Do not proceed until the user confirms their selections.

### 7. Generate FEAT IDs

For each accepted feature:
1. Start from the highest existing FEAT-* ID + 1
2. Assign sequential IDs: `FEAT-XX`, `FEAT-XX+1`, etc.
3. Confirm the ID assignments with the user

### 8. Update Documents

Prepare updates for all three roadmap files:

**`docs/PRODUCT_SENSE.md`:**
- Move completed features from planned lists to a "Completed" or "Shipped" section
- Add new accepted features to the appropriate priority tier (P0/P1/P2)
- Remove or retire stale items that are no longer relevant
- Preserve the document's existing voice and structure

**`docs/PLANS.md`:**
- Update phase statuses (mark completed phases, advance current phase)
- Add new features to existing phases or create new phases as appropriate
- Include brief rationale for new additions

**`docs/exec-plans/tech-debt-tracker.md`:**
- Add new `FEAT-*` rows for each accepted feature
- Use the standard row format matching existing entries
- Set status to `todo`, assign appropriate priority and area

### 9. Preview & Confirm

Show the user a diff summary of all planned changes:
```
## Planned Changes

### docs/PRODUCT_SENSE.md
- Added X new features to P0/P1/P2
- Moved X completed features to Shipped
- Retired X stale items

### docs/PLANS.md
- Updated phase X status to complete
- Added X new features to phase Y

### docs/exec-plans/tech-debt-tracker.md
- Added X new FEAT-* rows: FEAT-XX through FEAT-YY
```

Get final approval before writing any changes.

### 10. Write Changes

Apply all edits to the three files using the Edit tool. Do not modify any other files. Do not touch source code.

### 11. Branch, Commit, PR, Merge

1. Create branch: `git checkout -b chore/roadmap-$(date +%Y%m%d)`
2. Stage files explicitly by name — never `git add .` or `git add -A`:
   ```bash
   git add docs/PRODUCT_SENSE.md docs/PLANS.md docs/exec-plans/tech-debt-tracker.md
   ```
3. Commit with descriptive message:
   ```
   chore: strategic roadmap update — add X new features

   Research-driven roadmap refresh. Added FEAT-XX through FEAT-YY
   based on competitor analysis and ecosystem trend research.
   ```
4. Push and create PR with research summary in the description
5. After PR approval, squash merge to main
6. Pull main and verify:
   ```bash
   git checkout main && git pull origin main
   ```

## Important Rules

- **WebSearch is required** — do not skip the research phase or fabricate trends
- **Interactive approval is required** — never add features without user confirmation
- **Stage files explicitly** — never `git add .` or `git add -A`
- **Cite research** — every proposed feature must reference specific findings
- **Calibrate effort** — compare against completed tasks of similar scope in the tracker
- **No code changes** — this command only modifies documentation files
- **Respect existing structure** — preserve each document's voice, formatting, and organization
- **Domain-aware research** — tailor all web searches to the project's specific domain, not a generic one

## Cadence

- Run quarterly or when the roadmap feels stale
- Run after completing a major phase or milestone
- Run when significant market shifts occur (new competitor, new capability in the ecosystem)
- Human-triggered only — this command is never auto-triggered

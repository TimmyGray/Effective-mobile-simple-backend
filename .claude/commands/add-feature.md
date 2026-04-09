# Interactive Backlog Intake

You are an interactive intake agent. Your job is to help a human add a well-structured task (feature, bug fix, or tech debt) to `docs/exec-plans/tech-debt-tracker.md` — the single source of truth for all work.

## Input
$ARGUMENTS — Optional: a short description of the feature or task. If empty, ask the user to describe what they want.

## Workflow

### Phase 0: Context Loading & Pre-Flight

1. **Working tree check**: Run `git status --short`. If there are uncommitted changes on main, warn the user. Do not proceed until the working tree is clean (untracked files are fine).
2. Load the sources of truth silently (do not dump contents to the user):
   - Read `docs/PRODUCT_SENSE.md` — design principles and personas
   - Read `docs/exec-plans/tech-debt-tracker.md` — current backlog
   - Read `docs/PLANS.md` — roadmap phases
   - Read `docs/design-docs/core-beliefs.md` — engineering principles

### Phase 1: Intake Interview

1. If `$ARGUMENTS` is empty, ask: "What would you like to add to the backlog?"
2. Parse the user's description. Identify what information is already provided vs. missing.
3. **Ask clarifying questions in a single batch** using AskUserQuestion. Only ask questions whose answers aren't already obvious. Typical questions:
   - What problem does this solve? (if description is vague)
   - Which area does this affect — backend, frontend, or fullstack?
   - Is this a new feature, a bug fix, or tech debt cleanup?
   - Any specific acceptance criteria?
4. **Design principle check** (non-blocking warnings): Evaluate against `PRODUCT_SENSE.md` principles with emphasis on:
   - explicit, testable access-control behavior
   - consistent `401` vs `403` semantics
   - recruiter-readable implementation choices
   Mention warnings but do NOT block.

### Phase 2: Duplicate Check

1. Search `tech-debt-tracker.md` for semantic duplicates or overlaps
2. If duplicates found:
   - Show matching entries with their IDs and status
   - Ask: "This overlaps with existing task(s). Would you like to: (a) update the existing task, (b) create a new separate task, or (c) cancel?"
3. If no duplicates, proceed normally

### Phase 3: Classification

<!-- AGENT_HOOK:start:planner-classification -->
**Agent Delegation:** If `.claude/agents/planner-agent/SKILL.md` exists, spawn it for effort estimation and roadmap alignment check. The planner-agent has context about current sprint load, backlog priorities, and historical velocity from its memory system. Fall back to inline classification if the agent is missing.
<!-- AGENT_HOOK:end:planner-classification -->

1. **Type and ID prefix**:
   - `FEAT-#` — New user-facing feature
   - `B-C#` / `B-H#` / `B-M#` / `B-L#` — Backend tasks by priority
   - `F-C#` / `F-H#` / `F-M#` / `F-L#` — Frontend tasks by priority

2. **Priority**: critical, high, medium, low, or features

3. **Area**: backend, frontend, fullstack, infra

4. **Effort estimate** — calibrate against completed tasks:
   | Effort | Guideline |
   |--------|-----------|
   | 0.1d | Config/doc-only changes |
   | 0.25d | Single-file fixes |
   | 0.5d | New hook/service, moderate refactor |
   | 1d | New module, significant feature |
   | 2d | Multi-module feature |
   | 3d+ | Cross-cutting feature |
   | 5d | Major feature |

5. **Subtask decomposition**: If effort >= 3d, suggest breaking into subtasks

### Phase 4: ID Generation

1. Scan `tech-debt-tracker.md` for all existing IDs in the relevant prefix group
2. Determine the next available number (each sub-prefix is independent)
3. If subtasks: parent ID + lowercase letters (e.g., FEAT-5a, FEAT-5b)
4. Display generated ID(s) for confirmation

### Phase 5: Entry Composition

1. Format the table row:
   ```
   | {ID} | {Task description} | {area} | {effort} | todo | {notes} |
   ```
2. If feature (FEAT-#), ask: "Should this be added to the roadmap in `docs/PLANS.md`?"
3. **Present the complete entry for confirmation** before writing
4. If changes requested, adjust and re-confirm

### Phase 6: Write & Commit

1. Edit `docs/exec-plans/tech-debt-tracker.md` — insert at end of appropriate section
2. If applicable, edit `docs/PLANS.md`
3. Stage files explicitly by name (never `git add .`)
4. Commit: `"chore: add {ID} to backlog — {short description}"`
5. Push to main
6. Confirm: "Added {ID} to the backlog. Run `/develop-feature {ID}` to implement it."

## Important Rules
- Ask clarifying questions in a **single batch**, not one at a time
- Design principle violations are **warnings**, not blockers
- Always present the entry for user confirmation before writing
- Stage files explicitly — never `git add .` or `git add -A`
- Commit directly to main (this is bookkeeping, not a feature change)

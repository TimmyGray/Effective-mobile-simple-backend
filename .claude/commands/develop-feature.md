# Autonomous Feature Development

You are an autonomous development agent. Your job is to pick a task, implement it end-to-end, create a PR, monitor CI, fix failures, and merge — all without human intervention.

## Input
$ARGUMENTS — Optional task ID from `docs/exec-plans/tech-debt-tracker.md`. If empty, pick the next unstarted highest-priority task.

## Workflow

### Phase 0: Concurrency Setup

Before task selection, set up for safe parallel execution with other agents. **Phases 0-1 must run in the main repo** (before entering a worktree) because `active-work.json` is gitignored and only exists in the main working tree.

> **Sandbox note**: When the agent starts inside a worktree, the sandbox's `.` scope covers only the worktree directory. All writes to `active-work.json` in the main repo (and `git fetch` which writes `FETCH_HEAD`) require `dangerouslyDisableSandbox: true` on Bash calls. This applies to Phases 0, 1 (registry write), 1.5 (git fetch), and 11 (unregister).

1. Read `docs/exec-plans/active-work.json`. If the file is missing or corrupt, back up the corrupt file (`cp active-work.json active-work.json.bak 2>/dev/null || true`), then create a fresh file with: `{"schema_version":1,"sessions":[]}`
2. **Stale cleanup**: For each session entry:
   - If `started_at` is older than 24 hours → remove the entry (safety net for crashed sessions)
   - Otherwise, treat the entry as **active** — do not remove it
3. Write the cleaned registry using atomic rename: write to `active-work.json.tmp`, then `mv active-work.json.tmp active-work.json`
4. **Port allocation**: Find the lowest available slot number (0, 1, 2, ...) not used by any remaining session. Backend default is **8000** (Django dev server). For parallel agents, use `python manage.py runserver 0.0.0.0:$((8000 + slot))`.
5. Note the list of currently active `task_id`s — these are off-limits for task selection
6. Store the allocated ports and slot number for use in later phases

### Phase 1: Task Selection
1. Read `docs/exec-plans/tech-debt-tracker.md`
2. If task ID provided, find that task. Otherwise, select the next task with status `todo` and highest priority (critical > high > medium > low)
3. **Skip active tasks**: When selecting the next `todo` task, skip any task whose ID appears in the active-work registry (from Phase 0 step 5). If a specific task ID was provided via `$ARGUMENTS` and it's already active in the registry, **warn and stop**
4. Display the selected task and confirm understanding
5. **Register in active-work registry**: Add a session entry to `docs/exec-plans/active-work.json` with:
   - `task_id`: the selected task ID
   - `branch`: the branch name to be created (e.g., `feat/<kebab-case-task-name>`)
   - `started_at`: current ISO 8601 timestamp
   - `ports`: `{"backend": <allocated_backend_port>}`
6. Write the updated registry using atomic rename (write to `.tmp`, then `mv`)
7. **Post-write verification**: Re-read `active-work.json` and confirm that:
   - Own entry is present
   - No other entry has the same slot or task_id
   - If a conflict is detected, pick a new slot/task and retry from step 1 (max 3 retries)

### Phase 1.5: Worktree Isolation

Isolate the working tree so multiple `/develop-feature` agents can run concurrently without branch conflicts.

1. **Store main repo root** for later reference: Run `git rev-parse --show-toplevel` and remember this path
2. **Enter an isolated worktree** using the `EnterWorktree` tool with `name: "feat-<task-kebab>"`. This creates a fresh copy of the repo at `.claude/worktrees/<name>/` with its own branch.
   - If `EnterWorktree` fails, skip — the agent is already isolated
3. **Verify isolation**: Run `git rev-parse --show-toplevel` and confirm the path contains `.claude/worktrees/`
4. **Install dependencies**: Run dependency install commands appropriate for the project (e.g., `npm install`, `pip install -r requirements.txt`, etc.)
5. **Sync remote refs**: Run `git fetch origin main` to ensure `origin/main` is up-to-date. **Never run `git checkout main`** inside a worktree.

### Phase 2: Context Gathering
1. Read `ARCHITECTURE.md` for system overview
2. Based on the task area:
   - Backend work → read relevant backend source files
   - Frontend work → only if frontend exists in this repo
   - Full-stack → read all of the above
3. Read `docs/design-docs/core-beliefs.md` for engineering principles
4. Read `docs/CONVENTIONS.md` for code standards

### Phase 3: Branch & Plan
1. Create a feature branch: `git checkout -b feat/<kebab-case-task-name> origin/main`
2. **Execution Plan (required for tasks > 1 day effort)**:
   - Create `docs/exec-plans/active/<feature>.md` with:
     - Task description and acceptance criteria
     - Implementation phases with estimated effort
     - Files to create/modify
     - Decision log (fill in as you make choices)
     - Risks and open questions
3. Plan the implementation: list files to create/modify, tests to write

### Phase 4: Implementation

<!-- AGENT_HOOK:start:implementation-routing -->
**Agent Delegation:** Before implementing, detect the task area. If specialist agents exist in `.claude/agents/`:
- Backend-only task → read `.claude/agents/backend-agent/SKILL.md` and delegate implementation
- Frontend-only task → only if a frontend module exists; otherwise treat as unsupported and refocus to backend/infrastructure
- Full-stack task → spawn both as parallel Task subagents, each handling their domain
If agents don't exist or Task subagents are unavailable, follow the inline instructions below.
<!-- AGENT_HOOK:end:implementation-routing -->

1. Implement the changes following project conventions (see `docs/CONVENTIONS.md`)
2. Write tests for new functionality
3. Follow patterns from `docs/references/` if applicable
4. **Update execution plan** after each significant decision

### Phase 5: Validation + Staged-File Completeness
1. Run validation checks — fix failures, max 3 retries per check:
   ```
   npm run validate
   ```
   Or run individual checks as defined in your project's validate command.
2. After all checks pass, run **staged-file completeness check**:
   - Run `git status --short`
   - For each `??` (untracked) file, check if any file you modified/created imports it
   - For each ` M` (unstaged modified) file, check if it was changed during implementation
   - If an untracked/unstaged file is imported by any changed file, stage it immediately
   - After staging any new files, re-run typecheck and build to confirm clean state
3. This step prevents CI failures caused by files that exist on disk but aren't committed

### Phase 6: Deep Validation (Port-Aware)

Use the ports allocated in Phase 0. This ensures multiple agents can run dev servers simultaneously.

1. Start backend dev server in background on allocated port (for Django: `python manage.py runserver 0.0.0.0:<port>`).
2. Wait until server is ready (poll URL/log line, max 60s for cold start).
3. Run API validation for changed behavior (curl/httpie/pytest integration tests).
4. Verify expected auth semantics:
   - Unauthenticated access returns `401`.
   - Authenticated but unauthorized access returns `403`.
5. Check server output for tracebacks/errors.
6. Kill the started dev server process by PID when validation is done.
7. If validation reveals critical issues, fix and return to Phase 5 (max 3 retry cycles).

### Phase 7: Commit & PR
1. Run `git status --short` one final time
2. **Working directory assertion**: Confirm you're at the repo root
3. Stage each file explicitly by name (never `git add .` or `git add -A`)
4. Cross-check: `git diff --cached --name-only` includes all files created/modified
5. Commit with a descriptive message focused on "why"
6. Push: `git push -u origin feat/<branch-name>`
7. Create PR via `gh pr create` with summary and test plan

### Phase 8: CI Monitor & Fix Loop

This phase handles CI only. The code review lives entirely in Phase 9.

1. **Classify CI**: After `sleep 10`, run `gh pr checks <PR#>` (once).
   - **Checks present** → `gh pr checks <PR#> --watch --interval 30` until completion. Record `ci_status: pass` or `ci_status: fail`.
   - **No checks** (empty / "no checks reported") → record `ci_status: none`. Do **not** wait.
2. If `ci_status: none` → proceed directly to Phase 9.
3. If `ci_status: pass` → proceed to Phase 9.
4. If `ci_status: fail`:
   - Read failure logs: `gh run view <RUN_ID> --log-failed`
   - Analyze and fix the code
   - Stage, commit, push the fix
   - Return to step 1 (max 3 CI fix cycles)
5. If CI still fails after 3 cycles, stop and report the blocker.

### Phase 9: Quality Gate — Full `review-pr` (merge gate)

**Hard rule — do not enter Phase 10 until this phase yields `VERDICT: APPROVE`.**

The quality gate is **always** a full execution of `.claude/commands/review-pr.md`. There are no shortcuts — an informal skim, a mental check, or a single-agent summary does **not** satisfy this phase.

> **Why always full?** When `ci_status: none` (no GitHub Actions configured), this review is the **only** automated quality signal before merge. Even when CI passes, it only validates lint/types/build — not security, conventions, or architectural fitness. The four-lane structured review catches what CI cannot.

<!-- AGENT_HOOK:start:reviewer-delegation -->
**Agent Delegation:** If `.claude/agents/reviewer-agent/SKILL.md` exists, use it to coordinate the review. The reviewer-agent has project-specific convention knowledge and will further delegate the 4 review lanes to specialists as defined in `review-pr.md`. Fall back to generic `generalPurpose` subagents if the reviewer-agent is missing.
<!-- AGENT_HOOK:end:reviewer-delegation -->

#### 9.1 Execute `review-pr.md`

Read `.claude/commands/review-pr.md` and follow **every** step:

1. **Gather changes**: `gh pr diff <PR#>` and `gh pr view <PR#>` (or `git diff <base>...HEAD` if PR metadata is unavailable).
2. **Launch the four parallel review lanes** (review-pr § 2):
   - Use **parallel Task subagents** (`subagent_type: "generalPurpose"`) — one per lane (Security, Quality, Patterns, Testing).
   - Each subagent receives: (a) the full diff text, (b) the lane-specific checklist from `review-pr.md`, and (c) paths to the context docs it must read (e.g. `docs/SECURITY.md`, `docs/CONVENTIONS.md`, `docs/PRODUCT_SENSE.md`, `docs/RELIABILITY.md`).
   - If the Task tool is unavailable (e.g. readonly mode), perform all four reviews **sequentially in-context** — still follow every checklist item in `review-pr.md`.
3. **Aggregate** and deduplicate findings per review-pr § 3.
4. **Emit verdict** per review-pr § 4 on its own line: exactly `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`.

#### 9.2 Verdict handling

- `VERDICT: APPROVE` → proceed to Phase 10.
- `VERDICT: REQUEST_CHANGES`:
  1. Fix all blocking issues (critical + warning severity).
  2. Stage, commit, push fixes.
  3. **Re-entry depends on `ci_status`:**
     - `ci_status` was `pass` or `fail` → return to **Phase 8 step 1** (re-check CI on the new push, then re-enter Phase 9.1).
     - `ci_status` was `none` → return to **Phase 9.1** directly (no CI to re-check).
  4. On every re-review, run the **full four-lane review again** — never reuse a previous verdict for code that changed.
  5. Max **2 review-fix cycles** total. If still `REQUEST_CHANGES` after 2 cycles, stop and report remaining issues.

### Phase 9b: Root Cause Analysis & Immediate Learning

**Activation**: Only when Phase 9 had `REQUEST_CHANGES` (skip if APPROVE on first pass).

1. **Collect findings**: Gather all critical/warning findings from reviews
2. **Classify each by root cause category**:
   - `CONV` — Convention gap
   - `OVER` — Overgeneralization
   - `RAIL` — Missing guard rail (no lint rule/test)
   - `PROC` — Workflow/process bug
   - `MODEL` — Incomplete mental model
   - `COPY` — Copy-paste drift
3. **Write structured entries** to `pitfalls.md` in the Claude Code auto-memory directory
4. **Check promotion threshold**: If 2+ occurrences of the same category, promote:
   - `CONV` → Update `docs/CONVENTIONS.md` + `review-pr.md` agent prompt
   - `RAIL` → Add lint rule or architecture test
   - `PROC` → Add safeguard to `develop-feature.md`
5. **Append root cause summary** to the PR description

### Phase 10: Manual Merge Readiness (Auto-Merge Disabled)

**Precondition:** Phase 9 ended with `VERDICT: APPROVE` for the current head of the PR branch. If not, return to Phase 9.

1. Verify PR is mergeable and up to date: `gh pr view --json mergeable,mergeStateStatus,url`
2. If branch is behind, rebase onto `origin/main`, resolve conflicts, run validation, and push.
3. Post final readiness report including:
   - PR URL
   - CI/check status
   - Review verdict
   - Any residual risks or manual verification notes
4. Stop and leave the PR open for human approval and merge.

### Phase 11: Bookkeeping (Post-Merge)

> **Important**: All Phase 11-12 operations run from the **main repo working tree**.

1. Update task status in `docs/exec-plans/tech-debt-tracker.md` to `done`
2. If an exec plan was created, move it to `docs/exec-plans/completed/`
3. Stage bookkeeping files explicitly, commit, push
4. **Unregister from active-work registry**: Remove own entry from `active-work.json`

### Phase 12: Maintenance Cadence Check

<!-- AGENT_HOOK:start:planner-maintenance -->
**Agent Delegation:** If `.claude/agents/planner-agent/SKILL.md` exists, spawn it for maintenance cadence assessment. It has cross-session memory of sprint state and can make smarter decisions about which maintenance tasks are overdue.
<!-- AGENT_HOOK:end:planner-maintenance -->

1. Read `docs/exec-plans/maintenance-cadence.json`
   - If missing, create with default thresholds (sweep: 3, audit: 5, retrospective: 10)
2. **Recovery check**: If `pending_runs` is non-empty, re-launch them now
3. Increment all three counters by 1
4. Determine which maintenance tasks are due (counter >= threshold)
5. Reset due counters to 0, update `last_runs` dates
6. Write `pending_runs`, commit and push
7. **Launch due maintenance as parallel background Task subagents**:
   - **Sweep**: "Read `.claude/commands/sweep.md` and execute all instructions."
   - **Audit + Doc-garden**: "Read `.claude/commands/audit-service.md` and execute. Then read `.claude/commands/doc-garden.md` and execute."
   - **Retrospective**: "Read `.claude/commands/retrospective.md` and execute all instructions."
8. Clear `pending_runs`, commit and push
9. If no maintenance due, report the countdown

## Important Rules
- Never skip validation. Fix errors before creating the PR.
- **Never merge (Phase 10) without `VERDICT: APPROVE` from Phase 9.** Phase 9 always executes the full `.claude/commands/review-pr.md` — there is no shortcut path, regardless of CI status.
- Stage files explicitly — never use `git add .` or `git add -A`
- If a task touches > 15 files, break it into subtasks first
- If tests fail after 3 attempts, stop and report the issue
- The staged-file completeness check is critical — it prevents the #1 cause of CI failures
- Max retry limits are hard limits: do not exceed them
- Execution plans are living documents: update as you make decisions
- Auto-merge is disabled for this repository; never merge automatically from this workflow

# Autonomous Development Workflow

This project uses a self-improving autonomous loop with human steering.

## Workflow Loop

```
User idea → /add-feature → tech-debt-tracker.md → /develop-feature → /validate → /review-pr → PR merge
                                                         ↑                                       |
                                                         |                                       ↓
                                               /audit-service ← ← ← ← ← ← ← ← /retrospective
                                               /doc-garden + /sweep (continuous)
```

## Commands

| Command | Purpose | Cadence |
|---------|---------|---------|
| `/setup-workflow` | First-time project setup | Once |
| `/add-feature` | Interactive backlog intake | On demand |
| `/develop-feature [ID]` | Autonomous end-to-end feature dev | On demand |
| `/validate` | Full CI pipeline locally | Before every PR |
| `/review-pr [PR#]` | Multi-agent self-review | After implementation |
| `/audit-service` | Codebase audit + metrics | Every 5 features |
| `/sweep` | Golden principles enforcement | Every 3 features |
| `/doc-garden` | Documentation freshness scan | With audits |
| `/retrospective` | Workflow self-improvement | Every 10 features |
| `/update-roadmap` | Strategic roadmap refresh | Quarterly (manual) |

## Maintenance Cadence

Maintenance runs are triggered automatically by `/develop-feature` after each merge:

- `/sweep` every **3** features
- `/audit-service` every **5** features
- `/doc-garden` runs with audits
- `/retrospective` every **10** features

State is tracked in `docs/exec-plans/maintenance-cadence.json` (committed to git).

## Parallel Execution Architecture

### Active Work Registry

`docs/exec-plans/active-work.json` (gitignored) tracks running agents:
- Task ID, PID, allocated ports, timestamp
- Prevents concurrent agents from picking the same task
- Auto-cleanup for stale sessions (>24h)

### Port Allocation

When multiple agents run simultaneously, each gets unique ports:
- Slot 0: default ports (e.g., backend 3001, frontend 5173)
- Slot 1: backend +1, frontend +1
- General formula: `base_port + slot`

### Worktree Isolation

Each `/develop-feature` creates an isolated worktree at `.claude/worktrees/<name>/`:
- Eliminates branch/file conflicts between agents
- Phases 0-1 run in main repo (for shared registry)
- Phase 1.5 enters the worktree
- After merge, agent returns to main repo

### Concurrency Safety

- **Working tree isolation**: Each agent runs in its own git worktree — no branch or file conflicts
- **Task selection**: Agents skip tasks that are already active in the registry
- **Dev servers**: Each agent uses its allocated ports — no conflicts
- **Maintenance counters**: Slight over-counting from concurrent agents is acceptable and self-correcting (maintenance runs slightly more often)
- **Maintenance launches**: Before launching maintenance tasks, agents re-read `pending_runs` to avoid double-launching
- **Merge conflicts**: If merge fails due to conflicts from another recently-merged PR, the agent rebases and retries
- **Branch not up to date**: If `gh pr merge` fails with "head branch is not up to date", follow the recovery steps in the **PR Merge Recovery** section below

## PR Merge Recovery

If `gh pr merge` fails with **"the head branch is not up to date with the base branch"**, the feature branch is behind `main`. Follow these steps:

1. **Fetch and rebase onto main**
   ```bash
   git fetch origin main
   git rebase origin/main
   ```
2. **Resolve conflicts** — if the rebase produces conflicts, resolve them, `git add` the fixed files, and `git rebase --continue`
3. **Run validation** — run the project's validation suite to confirm nothing broke
4. **Force-push the updated branch** — `git push --force-with-lease`
5. **Wait for CI** — let any required checks pass on the updated branch
6. **Retry the merge** — `gh pr merge <PR#> --squash --delete-branch`

This is the expected recovery path when `main` has advanced since the branch was created (e.g., another PR was merged first). Do not use `--admin` to bypass branch protection.

## Guiding Principles

1. **Humans steer, agents execute** — humans set direction, agents handle implementation
2. **When agents fail, fix the environment** — improve tooling, not agent behavior
3. **Encode taste into tooling** — repeated review findings become lint rules
4. **Corrections cheap, waiting expensive** — fast merge/fix paradigm
5. **Repository is system of record** — all context lives in the repo
6. **Progressive disclosure** — small stable entry points (CLAUDE.md ~60 lines)
7. **Continuous garbage collection** — incremental debt paydown
8. **Parallelism over sequencing** — concurrent agents when possible

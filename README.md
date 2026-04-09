# Claude Code Workflow Kit

A production-grade autonomous development workflow for [Claude Code](https://claude.ai/claude-code). Copy this into any project to get a self-improving, agent-driven development loop with automated maintenance, quality enforcement, and documentation gardening.

## What This Is

This is a **generic, reusable workflow system** extracted from a battle-tested production project. It turns Claude Code into an autonomous development agent that can:

- Pick tasks from a backlog and implement them end-to-end
- Create PRs, monitor CI, self-review, and auto-merge
- Continuously scan for technical debt and fix it
- Keep documentation in sync with code
- Learn from its own mistakes and promote findings into lint rules
- Generate and delegate to project-aware specialist subagents (e.g., frontend, architect)

## The Workflow Loop

```
User idea → /add-feature → backlog → /develop-feature → /validate → /review-pr → PR merge
                                           ↑                                         |
                                           |                                         ↓
                                   /audit-service ← ← ← ← ← ← ← ← ← /retrospective
                                   /doc-garden + /sweep (continuous)
```

## Quick Start

### 1. Copy into your project

```bash
# Clone the kit
git clone https://github.com/TimmyGray/claude-code-workflow-kit.git /tmp/workflow-kit

# Copy into your project (from your project root)
cp -r /tmp/workflow-kit/.claude .
cp -r /tmp/workflow-kit/docs .
cp /tmp/workflow-kit/CLAUDE.md .
cp /tmp/workflow-kit/ARCHITECTURE.md .

# Clean up
rm -rf /tmp/workflow-kit
```

### 2. Run the setup command

Open Claude Code in your project and run:

```
/setup-workflow
```

This command will:
1. **Analyze your project** — read package files, source code, configs, git history
2. **Ask clarifying questions** — about deployment, team size, priorities, pain points
3. **Fill all documentation templates** — ARCHITECTURE.md, CONVENTIONS.md, SECURITY.md, etc.
4. **Adapt command files** — update validation commands, dev server ports, review checks
5. **Create initial backlog** — populate tech-debt-tracker with discovered issues and your priorities
6. **Run baseline validation** — capture initial quality metrics
7. **Commit everything** — ready to go

### 3. Generate agents and start developing

```
/generate-agents   # Create project-aware specialist agents (recommended)
/add-feature       # Add a task to the backlog
/develop-feature   # Pick the next task and implement it autonomously
```

## Commands Reference

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/setup-workflow` | Analyze project, fill docs, create roadmap | First time only |
| `/generate-agents` | Generate project-aware specialist agents | After setup or major tech changes |
| `/rollback-agents` | Undo command patches and optionally remove agents | If agent integration causes issues |
| `/add-feature` | Interactive backlog intake with duplicate detection | When you have a new idea |
| `/develop-feature [ID]` | Full autonomous dev: implement → test → PR → review → merge | To implement any task |
| `/validate` | Run lint + typecheck + test + build + staged completeness | Before any PR |
| `/review-pr [PR#]` | Multi-agent review (security, quality, patterns, tests) | After implementation |
| `/audit-service` | Comprehensive codebase audit + metrics update | Every 5 features (auto) |
| `/sweep` | Scan for principle violations, create micro-fix PRs | Every 3 features (auto) |
| `/doc-garden` | Fix stale/broken docs, validate cross-links | With audits (auto) |
| `/retrospective` | Analyze patterns, promote findings to lint rules | Every 10 features (auto) |
| `/i18n-dev` | i18n development guidelines | When adding UI strings |
| `/update-roadmap` | Research-driven strategic roadmap refresh | Quarterly or when roadmap feels stale |

## File Structure

```
your-project/
├── CLAUDE.md                          # Entry point (~60 lines, links to everything)
├── ARCHITECTURE.md                    # System architecture
├── docs/
│   ├── CONVENTIONS.md                 # Code conventions (enforced by lint)
│   ├── WORKFLOW.md                    # How the autonomous loop works
│   ├── SECURITY.md                    # Security model + threat model
│   ├── RELIABILITY.md                 # Error handling + logging
│   ├── PRODUCT_SENSE.md               # Vision, personas, feature priorities
│   ├── PLANS.md                       # Phased roadmap
│   ├── QUALITY_SCORE.md               # Metrics dashboard (auto-updated)
│   ├── DESIGN.md                      # UI/UX design system (frontend)
│   ├── design-docs/
│   │   └── core-beliefs.md            # 12 engineering principles
│   ├── exec-plans/
│   │   ├── tech-debt-tracker.md       # Machine-readable task backlog
│   │   ├── maintenance-cadence.json   # Maintenance state machine
│   │   ├── active-work.json           # Running agents registry (gitignored)
│   │   ├── active/                    # In-progress execution plans
│   │   └── completed/                 # Archived execution plans
│   └── references/                    # Framework/API reference docs
├── .claude/
│   ├── agents/                        # Generated specialist subagents (committed)
│   │   ├── _manifest.json             # Registry of available agents
│   │   ├── _patches.json              # Registry of patched commands
│   │   └── *-agent/                   # Subagent personas and capability files
│   └── commands/
│       ├── setup-workflow.md          # First-time project setup
│       ├── generate-agents.md         # Specialist agent generator
│       ├── rollback-agents.md         # Rollback agent patches
│       ├── add-feature.md             # Backlog intake
│       ├── develop-feature.md         # Autonomous feature dev (12 phases)
│       ├── review-pr.md              # Multi-agent PR review
│       ├── validate.md               # Validation suite
│       ├── sweep.md                  # Golden principles sweep
│       ├── audit-service.md          # Codebase audit
│       ├── doc-garden.md             # Documentation gardening
│       ├── retrospective.md          # Workflow retrospective
│       ├── i18n-dev.md               # i18n guidelines
│       └── update-roadmap.md        # Strategic roadmap refresh
└── .gitignore                         # Includes active-work.json, worktrees
```

## Key Design Decisions

### Progressive Disclosure
`CLAUDE.md` is a ~60-line table of contents, not an encyclopedia. Agents read it first, then dive into specific docs as needed. This keeps context windows clean.

### Repository as System of Record
All decisions, conventions, and state live in the repo. No Slack decisions, no tribal knowledge. The maintenance-cadence.json is committed to git so any agent in any session knows what maintenance is due.

### Encode Taste into Tooling
When a review finding appears 3+ times, `/retrospective` promotes it to a lint rule with a remediation message. Human taste is captured once, then enforced mechanically forever.

### Self-Improving Loop
```
Agent makes mistake → /review-pr catches it → pitfalls.md records it →
/retrospective analyzes patterns → ESLint rule created → mistake impossible
```

### Parallel Execution
Multiple `/develop-feature` agents can run simultaneously:
- **Worktree isolation**: Each agent gets its own working directory
- **Port allocation**: Slot-based system prevents dev server conflicts
- **Active work registry**: Prevents two agents from picking the same task

## Adapting to Your Stack

The kit is designed for **any tech stack**. The `/setup-workflow` command handles adaptation, but here's what gets customized:

| What | Default | Adapted To |
|------|---------|-----------|
| Validation commands | `npm run validate` | Your project's lint/test/build commands |
| Dev server ports | 3001 (backend), 5173 (frontend) | Your project's ports |
| Lint config references | ESLint | Your linter (Ruff, Clippy, etc.) |
| Test patterns | `*.spec.ts`, `*.test.tsx` | Your test file patterns |
| i18n system | react-i18next | Your i18n library (or disabled) |
| Architecture tests | TypeScript imports | Your language's module system |

## Maintenance Cadence

The system auto-maintains itself. After every feature merge, `/develop-feature` Phase 12 checks:

- **Every 3 features**: `/sweep` scans for principle violations
- **Every 5 features**: `/audit-service` + `/doc-garden` run comprehensive checks
- **Every 10 features**: `/retrospective` analyzes patterns and promotes lint rules

Thresholds are configurable in `docs/exec-plans/maintenance-cadence.json`.

## Philosophy

This workflow is built on these beliefs:

1. **Humans steer, agents execute** — you decide what to build, agents handle the how
2. **When agents fail, fix the environment** — improve tooling and docs, not agent prompts
3. **Corrections are cheap, waiting is expensive** — merge fast, fix fast
4. **Automate everything that can be automated** — lint rules > code review comments
5. **Small, focused changes** — one PR = one concern, max ~10 files

## License

MIT

# Codebase Audit

Perform a comprehensive audit of the codebase, update metrics, and identify new improvement tasks.

## Process

### 1. Automated Checks
Run and capture results (adapt commands to your project's stack):
- Security audit (e.g., `npm audit`, `pip audit`, `cargo audit`)
- Outdated dependencies check
- Lint: run linter and capture error count
- Typecheck: run type checker and capture error count
- Tests: run test suite and capture results
- Build: run build and verify success
- Bundle/artifact sizes

### 2. Code Quality Scan

<!-- AGENT_HOOK:start:audit-specialists -->
**Agent Delegation:** If specialist agents exist in `.claude/agents/`, delegate audit work:
- Code quality scan → `.claude/agents/architect-agent/SKILL.md` + `.claude/agents/tester-agent/SKILL.md` (parallel)
- Tech debt prioritization → `.claude/agents/planner-agent/SKILL.md`
Agents provide deeper project-specific context than generic inline scanning. Fall back to inline approach if agents are missing.
<!-- AGENT_HOOK:end:audit-specialists -->

Read source files and scan for:
- Anti-patterns (deeply nested callbacks, large files > 300 lines, functions > 50 lines)
- Missing error handling
- Hardcoded values that should be configurable
- Missing tests for critical paths
- Security issues (unsanitized input, exposed secrets)
- Dead code or unused exports

### 3. Update Quality Metrics
Update `docs/QUALITY_SCORE.md` with fresh data:
- Test count and pass rate
- Lint error count
- Type error count
- Bundle/artifact sizes
- Dependency freshness
- Known vulnerability count

### 4. Update Tech Debt Tracker
Compare findings against `docs/exec-plans/tech-debt-tracker.md`:
- Mark completed items as done
- Add new items discovered during audit
- Update priorities based on current severity

### 5. Report
Create a summary with:
- Overall health assessment (healthy, needs attention, critical)
- New issues found (count by severity)
- Metrics trends (improving, stable, degrading)
- Top 3 recommended next actions

### 6. Commit & PR
If any docs were updated:
1. Create branch: `git checkout -b chore/audit-$(date +%Y%m%d)`
2. Stage files explicitly, commit changes
3. Create PR with audit report as description

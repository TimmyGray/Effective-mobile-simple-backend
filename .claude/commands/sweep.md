# Golden Principles Sweep

Scan the codebase for deviations from golden principles, update quality grades, and open targeted micro-fix PRs.

## Philosophy

Technical debt is a high-interest loan — pay it down continuously in small increments rather than letting it compound. Human taste is captured once in golden principles, then enforced continuously on every line of code.

## Process

### 1. Load Golden Principles

Read these files to understand current standards:
- `docs/design-docs/core-beliefs.md` — engineering principles
- `docs/CONVENTIONS.md` — code conventions
- `docs/SECURITY.md` — security checklist

### 2. Scan for Violations

Run these scans across all source directories (exclude `node_modules`, `dist`, build artifacts):

<!-- AGENT_HOOK:start:sweep-specialists -->
**Agent Delegation:** If specialist agents exist in `.claude/agents/`, delegate scan categories:
- Code quality + pattern violations → `.claude/agents/reviewer-agent/SKILL.md`
- Architecture violations → `.claude/agents/architect-agent/SKILL.md`
- Test coverage gaps → `.claude/agents/tester-agent/SKILL.md`
Run as parallel Task subagents if available. Aggregate all findings before moving to prioritization step. Fall back to inline scanning if agents are missing.
<!-- AGENT_HOOK:end:sweep-specialists -->

**Code Quality Violations:**
- [ ] Files > 300 lines → should be split
- [ ] Functions/methods > 50 lines → should be decomposed
- [ ] Missing Python type hints on critical service boundaries → should be added
- [ ] Debug logging/prints in production paths → should use proper logger or remove
- [ ] Unused imports and dead code → should be removed
- [ ] Deeply nested callbacks (> 3 levels) → should be flattened

**Security Violations:**
- [ ] Hardcoded secrets, API keys, or credentials in source files
- [ ] Unsanitized user content rendered without escaping
- [ ] Missing input validation on API endpoints

**Pattern Violations:**
- [ ] Deviations from conventions documented in `docs/CONVENTIONS.md`
- [ ] Missing error handling on async operations
- [ ] Hardcoded values that should be configurable
- [ ] Missing centralized authorization checks on protected endpoints

**Architecture Violations:**
- [ ] Cross-module direct imports (bypassing proper dependency injection or module boundaries)
- [ ] Business logic in controllers/handlers (should be in services)
- [ ] Role/permission logic duplicated in multiple places instead of shared policy service

**i18n Violations (if applicable):**
- [ ] Hardcoded user-facing strings that should use translation system
- [ ] Translation keys missing in any locale file

### 3. Prioritize Findings

Categorize each finding:
- **Auto-fix** — can be fixed mechanically with no risk (unused imports, console.log removal)
- **Simple fix** — straightforward but needs verification (type annotations, error handling)
- **Needs design** — requires architectural thought (file splitting, module restructuring)

### 4. Create Micro-Fix PRs

For **auto-fix** findings:
1. Group related fixes (e.g., all unused imports in one PR)
2. For each group:
   - Create branch: `git checkout -b chore/sweep-<category>-$(date +%Y%m%d)`
   - Apply fixes
   - Run `npm run validate` (or project's validation command) to verify nothing breaks
   - Stage files explicitly, commit, push
   - Create PR with clear description
3. Each PR should be reviewable in under 1 minute

For **simple fix** findings:
- Add as new tasks to `docs/exec-plans/tech-debt-tracker.md` with priority `medium`

For **needs design** findings:
- Add as new tasks to `docs/exec-plans/tech-debt-tracker.md` with priority `low`

### 5. Update Quality Grades

After all fixes:
1. Run the full validation suite
2. Update `docs/QUALITY_SCORE.md` with new metrics
3. Always commit and push quality score updates

### 6. Report

Present a sweep summary:
```
## Sweep Report

### Scanned: X files
### Violations Found: X total
  - Auto-fixed: X (in Y PRs)
  - Added to tracker: X (simple fix)
  - Added to tracker: X (needs design)

### Quality Grade Changes:
  - [metric]: before → after

### PRs Created:
  - #N: [description]
```

## Cadence

- Run after every 2-3 features merged
- Run whenever quality metrics show degradation
- Run on demand as a quick cleanup pass

## Important Rules

- Never fix something that might change behavior without tests confirming correctness
- Always run validation after fixes — don't create PRs that break the build
- Keep each PR focused: one category of fix per PR
- Stage files explicitly — never `git add .` or `git add -A`
- If a fix touches > 5 files, split into multiple PRs

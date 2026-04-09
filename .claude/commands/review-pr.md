# PR Self-Review (Multi-Agent)

Review the current branch's changes against project standards using parallel specialized review agents.

## Input
$ARGUMENTS — Optional PR number. If empty, review the current branch's diff against main.

## Process

### 1. Gather Changes
If PR number provided:
- `gh pr diff $PR_NUMBER`
- `gh pr view $PR_NUMBER`

If no PR number:
- `git diff main...HEAD`
- `git log main..HEAD --oneline`

### 2. Parallel Specialized Reviews

Launch these reviews as parallel Task agents (`subagent_type: "generalPurpose"`). Each agent reviews the diff from a different perspective:

<!-- AGENT_HOOK:start:specialist-reviewers -->
**Agent Delegation:** If specialist agents exist in `.claude/agents/`, use them for review lanes:
- Agent A (Security) → `.claude/agents/architect-agent/SKILL.md` (has `docs/SECURITY.md` context)
- Agent B (Quality) → `.claude/agents/reviewer-agent/SKILL.md` (has `docs/CONVENTIONS.md` + core-beliefs context)
- Agent C (Patterns) → `.claude/agents/frontend-agent/SKILL.md` or `.claude/agents/backend-agent/SKILL.md` depending on diff content
- Agent D (Testing) → `.claude/agents/tester-agent/SKILL.md` (has `docs/RELIABILITY.md` + `QUALITY_SCORE.md` context)
Fall back to generic `generalPurpose` subagents if any specialist is missing.
<!-- AGENT_HOOK:end:specialist-reviewers -->

**Agent A: Security Review**
- Read `docs/SECURITY.md` for context
- Check: no secrets/API keys, input validation, path traversal, XSS, error leakage
- Severity: critical or warning only

**Agent B: Code Quality Review**
- Read `docs/design-docs/core-beliefs.md` and `docs/CONVENTIONS.md` for context
- Check: no unused imports, no `any` types, error handling, no hardcoded values
- Check: no cross-module imports, file size limits (300 lines), function size limits (50 lines)
- Check: proper logging (no console.log in production)
- Check: exported functions have assumptions that hold for ALL callers
- Check: functions adapted from another context still have valid assumptions (no copy-paste drift)
- Severity: critical, warning, or suggestion

**Agent C: Pattern & Convention Review**
- Read `docs/CONVENTIONS.md` for context
- Check: Django/DRF patterns (views/serializers/services separation, permission boundaries)
- Check: auth and authz logic is centralized and not duplicated ad hoc in handlers
- Check: HTTP semantics are correct (`401` unauthenticated, `403` forbidden)
- i18n checks are inactive for this backend-only repository
- Severity: critical or warning

**Agent D: Test Coverage Review**
- Read `docs/RELIABILITY.md` for context
- Check: new auth/authz logic has or updates tests when pytest is enabled
- Check: test file patterns `test_*.py` or `*_test.py` under backend app directories
- Severity: warning or suggestion

### 3. Aggregate Results

Collect all findings from the 4 agents. Deduplicate overlapping issues.

For each issue, report:
- File and line number
- Review agent (Security / Quality / Patterns / Testing)
- Severity (critical, warning, suggestion)
- Description and fix recommendation (with remediation instructions)
- **Root cause hint** (one-line analysis of why this mistake was likely made)

### 4. Verdict

Count blocking issues (severity: critical or warning):
- If 0 blocking issues: `VERDICT: APPROVE`
- If any blocking issues: `VERDICT: REQUEST_CHANGES`

End with the verdict on its own line.

**Important:** The verdict line must be exactly `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES` — this format is parsed by the autonomous pipeline (`/develop-feature`).

## Fix Loop (Autonomous Pipeline)

When run as part of `/develop-feature`:
1. The calling agent reads the `VERDICT:` line
2. If `REQUEST_CHANGES`, the caller fixes all blocking issues, commits, pushes, re-runs CI, re-runs this review
3. Max 2 review-fix cycles
4. Non-blocking suggestions don't trigger fix loops

## Review Quality Rules
- Be specific: cite exact file and line number
- Be actionable: every issue must include a concrete fix recommendation
- Remediation messages should be copy-pasteable guidance
- Don't flag stylistic preferences — only correctness, security, or maintainability
- When in doubt, mark as `suggestion` not `warning`

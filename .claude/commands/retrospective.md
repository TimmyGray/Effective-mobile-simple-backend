# Workflow Retrospective

Analyze recent development patterns, improve the autonomous development workflow, and **promote repeated review findings into mechanical enforcement**.

> "When documentation falls short, we promote the rule into code."

## Process

### 1. Gather Data
- `gh pr list --state merged --limit 10` — recent merged PRs
- For each PR: `gh pr view <number>` — read description, review comments
- Read `docs/QUALITY_SCORE.md` — current metrics
- Read `docs/exec-plans/tech-debt-tracker.md` — task completion rate

### 2. Analyze Patterns
Look for:
- **Repeated review issues:** Same type of issue flagged across multiple PRs
- **Scope problems:** PRs that were too large or touched too many areas
- **Test gaps:** Features merged without adequate tests
- **Validation failures:** Common lint/type/test errors that could be prevented
- **Command effectiveness:** Are the workflow steps catching issues?
- **Sweep findings:** Were the same violations found repeatedly?
- **Phase 9b entries:** Read `pitfalls.md` from auto-memory. Count by root cause category. Any category at 3+ that hasn't been promoted → escalate

### 3. Identify Improvements
For each pattern found, propose:
- Lint rule to catch it automatically
- CI check to prevent it
- Command modification to address it
- Core belief to add/update
- Reference doc to create/update

### 4. Promote Findings into Code (KEY STEP)

For any issue found 3+ times across PRs:

#### 4a. Promote to Lint Rule
1. Check if an existing lint rule covers it
2. If yes: enable/configure the rule
3. If no: use `no-restricted-syntax` or equivalent with a custom message
4. **The error message MUST include remediation instructions** — it will be shown to the agent

#### 4b. Promote to Structural Test
If the issue is an architectural violation:
1. Add a test that validates the invariant mechanically
2. Include a remediation message in the test failure output

#### 4c. Promote to CI Check
If the issue is a process violation:
1. Add a step to CI workflow or the `/validate` command

#### 4d. Update Documentation
If the issue reveals a documentation gap:
1. Update the relevant doc
2. Add a pointer from CLAUDE.md if the doc is new

#### 4e. Review Phase 9b Promotions
If a prompt-level promotion was previously made:
1. Check if the same category recurred → escalate to lint rule
2. If no recurrence → working as intended

### 5. Apply Improvements
- Update `.claude/commands/*.md` if workflow needs adjustment
- Update `docs/design-docs/core-beliefs.md` if new principles learned
- Update lint configs if new rules added
- Run validation to verify changes

### 6. Update Learning Memory
Write key learnings to Claude Code auto-memory files:
- `patterns.md` — successful patterns to repeat
- `pitfalls.md` — mistakes to avoid

### 7. Report
Present:
- PRs analyzed (count, date range)
- Patterns identified
- **Rules promoted** (with tracking table)
- Improvements proposed
- Changes made
- Metrics comparison (before vs after)

## Promotion Tracking

Keep a running log:
```
## Promoted Rules Log
| Date | Pattern | Promoted To | Rule/Test Name |
|------|---------|-------------|----------------|
```

## Cadence
Run every 5-10 features, or when quality metrics trend downward.

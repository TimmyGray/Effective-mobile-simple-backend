# Engineering Principles

These are the project's non-negotiable engineering beliefs. They guide every technical decision.

## 1. Simplicity Over Cleverness
Write straight code. Avoid premature abstractions. Three similar lines are better than a premature helper.

## 2. Validate at Boundaries, Trust Inside
Validate input at system boundaries (controllers, API handlers). Trust internal code paths.

## 3. Fail Fast, Fail Loud
Invalid config crashes at startup. Missing data throws immediately. Don't swallow errors silently.

## 4. Security is Non-Negotiable
No secrets in commits. Sanitize user content. Validate file paths. Rate limit endpoints.

## 5. Test What Matters
Business logic + edge cases. Regression tests for bugs. Integration > unit for APIs.

## 6. Consistent Patterns
Follow existing patterns in the codebase. Don't invent new approaches when established ones exist.

## 7. Small, Focused Changes
One PR = one concern. Max ~10 files per PR. Don't mix refactoring with feature work.

## 8. Automation Over Process
Lint/typecheck/test in CI. Pre-commit hooks. Commands automate the full workflow.

## 9. Agent Legibility First
Code optimized for agent comprehension. All context in repo. Boring tech choices.

## 10. Encode Taste into Tooling
3+ review findings of the same type become a lint rule. Human taste captured once, enforced continuously.

## 11. Continuous Garbage Collection
Pay technical debt incrementally. /sweep every 2-3 features. Never let debt compound.

## 12. Progressive Disclosure
CLAUDE.md is a ~60-line table of contents, not an encyclopedia. Small stable entry points. Structured docs/.

## Project-Specific Principles

### 13. Authorization is Data, Not If-Else Sprawl
Represent permissions in durable tables and evaluate them centrally. Do not scatter ad hoc role checks across handlers.

### 14. Soft Delete Means Access Revocation
When an account is deactivated, all active auth artifacts must become unusable immediately.

### 15. Recruitment-Test Clarity
Prefer clarity over novelty: reviewers must quickly see schema intent, policy flow, and error semantics.

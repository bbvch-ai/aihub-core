---
name: review-diff
description: Review the diff between the current branch and main as a senior developer. Analyzes architecture, coding standards, security, performance, and correctness. Use when user says 'review my code', 'pre-PR review', 'review diff', 'code review before PR', 'check my changes', 'senior review', or 'review branch'. Provides actionable feedback organized by severity. Do NOT use for only running tests (use /test-scope), only linting (use /lint), or full PR preparation (use /create-pr).
allowed-tools: Bash, Read, Grep, Glob
---

# Review Diff - Pre-PR Code Review

Perform a comprehensive code review of all changes between the current branch and main, as a senior developer would.

## Step 1: Gather the Diff

```bash
git diff main...HEAD
git diff main...HEAD --stat
git log main...HEAD --oneline
```

Read the full diff carefully. Understand every change before reviewing.

## Step 2: Read Affected CLAUDE.md Files

For each scope touched by the diff, read its `CLAUDE.md` to understand scope-specific conventions. The root `CLAUDE.md`
has 16 Coding Conventions — use those as the baseline for all reviews.

## Step 3: Review Checklist

### Architecture & Scope Boundaries

- Code is in the correct scope (shared code in `packages/core`, scope-specific code in its scope)
- No cross-scope imports (only through `packages/core`, exception: `packages/process` → `packages/agent`)
- Controller → Service → Entity separation respected (see `packages/api/swiss_ai_hub/api/routes/agent/` for reference)
- New entities use MongoEngine Documents in `packages/core/swiss_ai_hub/core/persistence/entities/`
- New events follow Swiss AI Agent Protocol hierarchy (Control vs Display, see `/validate-events`)

### Coding Standards (root CLAUDE.md rules 01-16)

Review against ALL 16 Coding Conventions in the root `CLAUDE.md`. Flag any violations. Pay special attention to rules
that are easy to miss in diffs:

- Cross-scope imports bypassing `packages/core` (rule 11 — linter won't catch this)
- Missing `@classmethod` factories on new Pydantic models (`from_entity()`, `from_request()`)
- `try-except` wrappers that swallow errors instead of failing fast (rule 03)
- Dataclasses or plain dicts used instead of Pydantic models (rule 02)
- New abstractions that don't follow existing patterns in the codebase (rule 16)

### Security (OWASP Top 10)

- No string concatenation in queries or shell commands
- Permission checks via `Security(self.user_with_permission(...))` on all new endpoints
- `AccessChecker.from_user(user).has_access_to_agent(...)` for fine-grained authorization
- Secrets use `SecretStr`, never plain strings
- No hardcoded credentials or tokens
- Input validation at system boundaries (FastAPI path/query params, Pydantic models)

### NATS & Event Patterns

- New events inherit from correct base (`ControlEvent` vs `DisplayEvent`)
- Event names follow `{Verb}{Noun}Event` convention
- NATS subjects follow `aihub.{scope}.{class}.{id}.{event}` pattern
- Subscribers use `AbstractSubscriber` / `AgentNCSubscriber` — not raw NATS subscriptions

### Testing

- New code has corresponding tests in the scope's `tests/` or `playground/testing/tests/` directory
- Tests are specific (not just "no exception") with meaningful assertions
- External services properly mocked (NATS, MongoDB, S3, LLM calls)
- BDD (pytest-bdd with `.feature` files) for complex agent/process workflows
- Test markers applied correctly (`slow`, `integration`, `flaky`)

## Step 4: Produce the Review

Organize findings by severity:

### Format

```
## Critical (must fix before merge)
- [file:line] Description of the issue and why it matters

## Important (should fix)
- [file:line] Description and suggestion

## Suggestions (nice to have)
- [file:line] Description and alternative approach

## What looks good
- Brief acknowledgment of well-done aspects
```

### Rules

- Be specific: reference exact files and line numbers
- Be constructive: suggest the fix, not just the problem
- Be honest: if the code is good, say so
- Focus on substance: skip nitpicks that formatters/linters catch (ruff handles formatting, imports, pyupgrade)
- Do NOT suggest adding backwards compatibility unless explicitly asked

## Examples

- `/review-diff` — Review all changes on the current branch vs main
- `/review-diff feat/new-agent` — Review a specific branch (if provided via \$ARGUMENTS)

## Troubleshooting

| Problem                            | Solution                                                     |
| ---------------------------------- | ------------------------------------------------------------ |
| No diff found                      | Ensure you are on a feature branch, not main                 |
| Diff is very large                 | Focus on architectural issues first, then drill into details |
| Cannot determine scope conventions | Read the scope's `CLAUDE.md` for patterns                    |

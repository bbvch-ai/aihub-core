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

Read the root `CLAUDE.md` first — it defines all coding conventions (rules 01-20) and testing standards. Then read each
affected scope's `CLAUDE.md` for scope-specific conventions.

## Step 3: Review Checklist

### Architecture & Scope Boundaries

- Code is in the correct scope (shared code in `aihub_lib`, scope-specific code in its scope)
- No cross-scope imports (only through `aihub_lib`, exception: `aihub_process` → `aihub_agent`)
- Controller → Service → Entity separation respected (see `aihub_api/aihub_api/routes/agent/` for reference)
- New entities use MongoEngine Documents in `aihub_lib/aihub_lib/persistence/entities/`
- New events follow Swiss AI Agent Protocol hierarchy (Control vs Display, see `/validate-events`)

### Coding Standards (root CLAUDE.md rules 01-20)

Review against ALL 20 Coding Conventions in the root `CLAUDE.md`. Flag any violations. Pay special attention to rules
that are easy to miss in diffs:

- Cross-scope imports bypassing `aihub_lib` (rule 11 — linter won't catch this)
- Missing `@classmethod` factories on new Pydantic models (`from_entity()`, `from_request()`)
- `try-except` wrappers that swallow errors instead of failing fast (rule 03)
- Dataclasses or plain dicts used instead of Pydantic models (rule 02)
- New abstractions that don't follow existing patterns in the codebase (rule 16)
- Business logic mixed with IO in the same function instead of separating concerns (rule 17)
- Methods using `self` that should be `@staticmethod` (rule 18)
- Private helpers defined above their public callers (rule 19)
- Opaque method names that require reading the body to understand intent (rule 20)

### Code Readability & Structure

- Functions over 30 lines: can they be decomposed into smaller named units? (rule 06: < 50 lines, but aim for
  single-responsibility)
- Mixed concerns: does a single function both compute results AND perform IO (database, network, file)? Split into a
  pure logic function and a thin IO caller (rule 17, see
  `aihub_lib/aihub_lib/generative_ai/retrieval/retrieve_nodes.py`)
- Function names describe WHAT they return or DO — not implementation details. Names should read like a sentence at the
  call site
- Deep nesting (> 3 levels): extract inner logic into named helper functions
- God methods: services or handlers that do too many things — split into focused methods that compose

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
- External services properly mocked (NATS, MongoDB, S3, LLM calls via `MagicMock`/`AsyncMock`/`patch`)
- BDD (pytest-bdd with `.feature` files) for complex agent/process workflows
- Test markers applied correctly (`slow`, `flaky`, `e2e`)
- Flag useless tests and missing edge cases per root `CLAUDE.md` Testing section

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

| Problem                            | Solution                                                                                    |
| ---------------------------------- | ------------------------------------------------------------------------------------------- |
| No diff found                      | Ensure you are on a feature branch, not main                                                |
| Diff is very large                 | Focus on architectural issues first, then drill into details                                |
| Cannot determine scope conventions | Read the scope's `CLAUDE.md` for patterns                                                   |
| Docker Compose or infra changes    | Run backup-coverage-checker agent to verify container lists and backup coverage are in sync |

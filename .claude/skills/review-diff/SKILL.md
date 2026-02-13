---
name: review-diff
description: >-
  Review the diff between the current branch and main as a senior developer. Analyzes architecture,
  coding standards, security, performance, and correctness. Use when user says 'review my code',
  'pre-PR review', 'review diff', 'code review before PR', 'check my changes', 'senior review',
  or 'review branch'. Provides actionable feedback organized by severity.
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

For each scope touched by the diff, read its `CLAUDE.md` to understand scope-specific conventions.

## Step 3: Review Checklist

### Architecture & Design
- Code is in the correct scope (shared code in aihub_lib, scope-specific code in its scope)
- No cross-scope imports (only through aihub_lib, exception: aihub_process → aihub_agent)
- Controller → Service → Entity separation respected
- One class per file, file name matches class name
- No standalone function files — use service classes
- No new abstractions that diverge from existing patterns
- No unnecessary backwards compatibility shims

### Coding Standards
- All parameters and returns have type annotations
- `Annotated` used for parameter metadata (not docstring `Args:` sections)
- Modern Python syntax: `str | None`, `list[str]`, `match/case`
- Pydantic models for all structured data (never dicts or dataclasses)
- Pydantic models have `@classmethod` factories (`from_entity()`, `from_request()`) where helpful
- Async for all I/O operations
- No defensive try-catch wrappers — fail fast
- No comments explaining "what" — only "why" when non-obvious
- Methods under 50 lines, low cognitive complexity
- Descriptive naming (no abbreviations)

### Security (OWASP Top 10)
- No string concatenation in queries or shell commands
- Permission checks via `Security(...)` on all endpoints
- Secrets use `SecretStr`, never plain strings
- No hardcoded credentials or tokens
- Input validation at system boundaries

### Correctness
- Edge cases handled
- Race conditions considered for async code
- Resource cleanup (connections, file handles)
- Error messages are helpful and specific

### Testing
- New code has corresponding tests
- Tests are specific (not just "no exception")
- External services properly mocked
- BDD for complex workflows

## Step 4: Produce the Review

Organize findings by severity:

### Format

```
## 🔴 Critical (must fix before merge)
- [file:line] Description of the issue and why it matters

## 🟡 Important (should fix)
- [file:line] Description and suggestion

## 🔵 Suggestions (nice to have)
- [file:line] Description and alternative approach

## ✅ What looks good
- Brief acknowledgment of well-done aspects
```

### Rules
- Be specific: reference exact files and line numbers
- Be constructive: suggest the fix, not just the problem
- Be honest: if the code is good, say so
- Focus on substance: skip nitpicks that formatters/linters catch
- Do NOT suggest adding backwards compatibility unless explicitly asked

## Examples

- `/review-diff` — Review all changes on the current branch vs main
- `/review-diff feat/new-agent` — Review a specific branch (if provided via $ARGUMENTS)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No diff found | Ensure you are on a feature branch, not main |
| Diff is very large | Focus on architectural issues first, then drill into details |
| Cannot determine scope conventions | Read the scope's `CLAUDE.md` for patterns |

---
name: test-scope
description: Detect affected scopes from git changes and run their tests in dependency order. Use when user says 'run tests', 'test my changes', 'check what broke', 'verify scopes', 'test affected packages', or 'make sure tests pass'. Supports explicit scope names or auto-detection from git diff. Reports PASS/FAIL per scope. Do NOT use for linting or formatting (use /lint), full PR preparation (use /create-pr), or debugging test failures (use /debug-agent or /debug-pipeline).
allowed-tools: Bash, Read, Grep, Glob
---

# Smart Scoped Test Runner

Run tests only for scopes affected by current changes. Scope names can be provided via `$ARGUMENTS` or auto-detected
from git diff.

## Scope Dependency Graph

```
packages/core ──→ packages/agent ──→ packages/process
    │              │
    ├──→ packages/api ┘
    ├──→ packages/bot
    └──→ packages/pipeline
```

## Step 1: Detect Affected Scopes

If `$ARGUMENTS` specifies scope names (e.g., `packages/api packages/agent`), use those directly. Otherwise auto-detect:

1. Run `git diff --name-only HEAD` to list staged + unstaged changed files
2. Map each changed file to its scope by extracting the first path component
3. Valid scopes: `packages/core`, `packages/agent`, `packages/api`, `packages/bot`, `packages/pipeline`,
   `packages/process`, `packages/web`
4. Ignore files not in a valid scope (e.g., root configs, docs)

**Expected output**: A list like `Detected affected scopes: packages/core, packages/api`

## Step 2: Expand Downstream Dependencies

Add downstream scopes that depend on any changed scope:

- `packages/core` changed → add ALL other scopes (it is the foundation)
- `packages/agent` changed → also add `packages/process` (process depends on agent)

## Step 3: Run Tests in Dependency Order

Execute `make test` in each affected scope's directory, following this order:

1. `packages/core` (foundation — test first)
2. `packages/agent`
3. `packages/pipeline`
4. `packages/process` (depends on agent)
5. `packages/api`
6. `packages/bot`
7. `packages/web` — run `make -C packages/web pr-ready` (ESLint, no pytest for frontend)

Skip scopes not in the affected set. If a scope fails, continue running remaining scopes to collect all failures.

## Step 4: Report Results

Produce a summary table:

| Scope         | Status | Details                    |
| ------------- | ------ | -------------------------- |
| packages/core | PASS   | 42 tests passed            |
| packages/api  | FAIL   | 2 failures in test_auth.py |
| packages/web  | SKIP   | Not affected               |

## Examples

- `/test-scope` — Auto-detect from git diff and run all affected
- `/test-scope packages/api` — Run tests only for packages/api
- `/test-scope packages/core` — Run tests for packages/core AND all downstream scopes
- `/test-scope packages/agent packages/api` — Run tests for both specified scopes

## Troubleshooting

- **"No changes detected"**: Ensure you have uncommitted changes. Run `git status` to verify.
- **"make test fails with ModuleNotFoundError"**: Dependencies may not be installed. Run `uv sync --all-packages` from
  the workspace root.
- **No root `make test` exists**: Each scope must be tested individually via `make -C <scope> test`.
- **Frontend scope**: `packages/web` has no pytest — `make -C packages/web pr-ready` runs ESLint instead.

---
name: test-scope
description: Detect affected scopes from git changes and run their tests in dependency order. Use when user says 'run tests', 'test my changes', 'check what broke', 'verify scopes', 'test affected packages', or 'make sure tests pass'. Supports explicit scope names or auto-detection from git diff. Reports PASS/FAIL per scope.
allowed-tools: Bash, Read, Grep, Glob
---

# Smart Scoped Test Runner

Run tests only for scopes affected by current changes. Scope names can be provided via `$ARGUMENTS` or auto-detected
from git diff.

## Scope Dependency Graph

```
aihub_lib ──→ aihub_agent ──→ aihub_process
    │              │
    ├──→ aihub_api ┘
    ├──→ aihub_bot
    └──→ aihub_pipeline
```

## Step 1: Detect Affected Scopes

If `$ARGUMENTS` specifies scope names (e.g., `aihub_api aihub_agent`), use those directly. Otherwise auto-detect:

1. Run `git diff --name-only HEAD` to list staged + unstaged changed files
2. Map each changed file to its scope by extracting the first path component
3. Valid scopes: `aihub_lib`, `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`, `aihub_process`, `aihub_web`
4. Ignore files not in a valid scope (e.g., root configs, docs)

**Expected output**: A list like `Detected affected scopes: aihub_lib, aihub_api`

## Step 2: Expand Downstream Dependencies

Add downstream scopes that depend on any changed scope:

- `aihub_lib` changed → add ALL other scopes (it is the foundation)
- `aihub_agent` changed → also add `aihub_process` (process depends on agent)

## Step 3: Run Tests in Dependency Order

Execute `make test` in each affected scope's directory, following this order:

1. `aihub_lib` (foundation — test first)
2. `aihub_agent`
3. `aihub_pipeline`
4. `aihub_process` (depends on agent)
5. `aihub_api`
6. `aihub_bot`
7. `aihub_web` — run `pnpm lint` in `aihub_web/aihub_web/` (no pytest for frontend)

Skip scopes not in the affected set. If a scope fails, continue running remaining scopes to collect all failures.

## Step 4: Report Results

Produce a summary table:

| Scope     | Status | Details                    |
| --------- | ------ | -------------------------- |
| aihub_lib | PASS   | 42 tests passed            |
| aihub_api | FAIL   | 2 failures in test_auth.py |
| aihub_web | SKIP   | Not affected               |

## Examples

- `/test-scope` — Auto-detect from git diff and run all affected
- `/test-scope aihub_api` — Run tests only for aihub_api
- `/test-scope aihub_lib` — Run tests for aihub_lib AND all downstream scopes
- `/test-scope aihub_agent aihub_api` — Run tests for both specified scopes

## Troubleshooting

- **"No changes detected"**: Ensure you have uncommitted changes. Run `git status` to verify.
- **"make test fails with ModuleNotFoundError"**: The Poetry virtualenv may not be active. Run `poetry install` in the
  scope directory first.
- **No root `make test` exists**: Each scope must be tested individually from its own directory.
- **Frontend scope**: `aihub_web` uses `pnpm lint`, not `make test`. Run from `aihub_web/aihub_web/`.

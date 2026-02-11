---
name: test-scope
description: Identify which scopes are affected by current changes and run their
  tests. Parses git diff to determine affected scopes, includes downstream dependents.
  Use after making code changes to verify nothing is broken.
allowed-tools: Bash, Read, Grep, Glob
---

# Smart Scoped Test Runner

Run tests only for scopes affected by current changes. Scope names can be provided via `$ARGUMENTS` or auto-detected.

## Scope Dependency Graph

```
aihub_lib ──→ aihub_agent ──→ aihub_process
    │              │
    ├──→ aihub_api ┘
    ├──→ aihub_bot
    └──→ aihub_pipeline
```

## Step 1: Detect Affected Scopes

If `$ARGUMENTS` specifies scope names, use those. Otherwise auto-detect:

1. Run `git diff --name-only HEAD` for staged + unstaged changes
2. Map each changed file to its scope (first path component)
3. Known scopes: aihub_lib, aihub_agent, aihub_api, aihub_bot, aihub_pipeline, aihub_process, aihub_web

## Step 2: Expand Downstream Dependencies

- aihub_lib changed → add ALL other scopes
- aihub_agent changed → also add aihub_process

## Step 3: Run Tests in Dependency Order

1. aihub_lib (foundation)
2. aihub_agent
3. aihub_pipeline
4. aihub_process (depends on agent)
5. aihub_api
6. aihub_bot
7. aihub_web (run `pnpm lint` in `aihub_web/aihub_web/`)

Run each scope's tests with `make test` from within the scope directory.

## Step 4: Report Results

Produce summary table with scope, status (PASS/FAIL/SKIP), and details.

## Important Notes

- No root `make test` exists — test each scope individually
- If a scope fails, continue running remaining scopes (collect all failures)
- For aihub_web, run `pnpm lint` (no pytest for frontend)

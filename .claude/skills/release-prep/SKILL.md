---
name: release-prep
description: Run comprehensive pre-release validation. Checks all scopes for
  formatting, linting, type checking, tests, documentation freshness, and
  version consistency. Use before merging to main or creating a release.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

# Pre-Release Validation

Run all quality gates before merge. Mode via `$ARGUMENTS` ("quick" for lint-only, or "full" for everything).

## Check 1: Format & Lint

```bash
cd /home/user/aihub-core && make pr-ready
```

Pass criteria: Zero errors after auto-fix.

## Check 2: Tests

Run in each scope individually:
```bash
cd /home/user/aihub-core/aihub_lib && make test
cd /home/user/aihub-core/aihub_agent && make test
cd /home/user/aihub-core/aihub_api && make test
cd /home/user/aihub-core/aihub_bot && make test
cd /home/user/aihub-core/aihub_pipeline && make test
cd /home/user/aihub-core/aihub_process && make test
```

## Check 3: Version Consistency

Read each scope's `pyproject.toml` for aihub-lib tag. Verify all match.

## Check 4: Git Cleanliness

No uncommitted changes. Commits follow conventional format. Branch up to date.

## Check 5: Compose Generation

```bash
cd /home/user/aihub-core && make generate-compose && git diff --stat
```

Pass: No diff after regeneration.

## Check 6: Documentation Freshness

Changed scopes have updated README.md. AGENTS.md files are accurate. ADRs exist for significant changes.

## Summary Report

Table with check name, status (PASS/FAIL/WARN/SKIP), and details.

## Quick Mode

If `$ARGUMENTS` contains "quick": only run Checks 1, 3, and 4.

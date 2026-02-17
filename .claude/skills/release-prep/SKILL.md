---
name: release-prep
description: Run comprehensive pre-release validation across all scopes. Checks formatting,
  linting, type checking, tests, version consistency, git cleanliness, compose generation,
  and documentation freshness. Use when user says 'prepare for release', 'pre-merge checks',
  'is this ready to merge', 'run all checks', 'pr-ready all scopes', or 'release validation'.
  Supports 'quick' mode for lint-only.
allowed-tools: Bash, Read, Grep, Glob
---

# Pre-Release Validation

Run all quality gates before merging to main or creating a release. Mode via `$ARGUMENTS`: `quick` (lint-only) or `full` (default, everything).

## Quick Mode

If `$ARGUMENTS` contains `quick`, run ONLY Checks 1, 3, and 4 (format/lint, version consistency, git cleanliness). Skip tests, compose generation, and documentation checks.

## Check 1: Format and Lint (All Scopes)

```bash
cd /home/user/aihub-core && make pr-ready
```

**Pass criteria**: Zero errors remaining after auto-fix completes.
**If it fails**: Review the error output. Common issues are import ordering (fixed by ruff) and type errors (require manual fixes).

## Check 2: Tests (All Scopes)

Run tests in each scope individually, in dependency order:

```bash
cd /home/user/aihub-core/aihub_lib && make test
cd /home/user/aihub-core/aihub_agent && make test
cd /home/user/aihub-core/aihub_api && make test
cd /home/user/aihub-core/aihub_bot && make test
cd /home/user/aihub-core/aihub_pipeline && make test
cd /home/user/aihub-core/aihub_process && make test
```

If a scope fails, continue running remaining scopes to collect all failures.

## Check 3: Version Consistency

1. Read each scope's `pyproject.toml`
2. Find the `aihub-lib` dependency Git tag
3. Verify all scopes reference the same tag

**Pass criteria**: All scopes use the identical aihub-lib version tag.

## Check 4: Git Cleanliness

1. `git status` — no uncommitted changes
2. `git log --oneline -5` — recent commits follow conventional format (`feat(scope):`, `fix(scope):`, etc.)
3. `git fetch origin && git status` — branch is up to date with remote

**Pass criteria**: Clean working tree, conventional commits, no divergence from remote.

## Check 5: Compose Generation

```bash
cd /home/user/aihub-core && make generate-compose && git diff --stat
```

**Pass criteria**: No diff after regeneration. If files changed, the compose templates were modified without regenerating.

## Check 6: Documentation Freshness

1. For each changed scope (from `git diff --name-only origin/main...HEAD`), verify its `README.md` is up to date
2. Check `CLAUDE.md` files are accurate for changed scopes
3. Verify ADRs exist in `/home/user/aihub-core/aihub_doc/arc42/decisions/` for any significant architectural changes

**Pass criteria**: Documentation reflects current code state.

## Summary Report

| Check | Status | Details |
|-------|--------|---------|
| Format & Lint | PASS | Zero errors |
| Tests | FAIL | aihub_api: 2 failures |
| Version Consistency | PASS | All scopes: v1.2.3 |
| Git Cleanliness | WARN | 1 uncommitted file |
| Compose Generation | PASS | No diff |
| Documentation | SKIP | No scope READMEs changed |

## Examples

- `/release-prep` — Full validation (all 6 checks)
- `/release-prep quick` — Quick validation (format/lint + version + git only)
- `/release-prep full` — Explicit full validation

## Troubleshooting

- **"make pr-ready" not found**: Ensure you are running from the repo root `/home/user/aihub-core/`, not a scope directory.
- **Tests fail with import errors**: Run `poetry install` in the failing scope first.
- **Compose generation shows diff**: Run `make generate-compose` and commit the regenerated files.
- **Version mismatch across scopes**: Update the lagging scope's `pyproject.toml` to reference the correct aihub-lib tag, then run `poetry lock --no-update`.

---
name: dependency-audit
description: Audit Python and Node.js dependencies for outdated packages, security
  vulnerabilities, license issues, and aihub-lib version consistency across scopes.
  Use when user says 'check dependencies', 'audit packages', 'find vulnerabilities',
  'outdated deps', 'license check', or 'are all scopes on the same aihub-lib version'.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

# Dependency Health Audit

Audit all project dependencies for outdated packages, vulnerabilities, and version consistency. Scope via `$ARGUMENTS`: a specific scope name (e.g., `aihub_api`), `frontend`, or `all` (default).

## Step 1: Audit Python Scopes

For each Python scope (`aihub_lib`, `aihub_agent`, `aihub_api`, `aihub_bot`, `aihub_pipeline`, `aihub_process`):

### 1a. Check for outdated packages

```bash
cd /home/user/aihub-core/<scope> && poetry show --outdated
```

Note the number of outdated packages and any major version jumps.

### 1b. Verify aihub-lib version consistency

1. Read each scope's `pyproject.toml`
2. Find the `aihub-lib` dependency line (look for the Git URL + tag)
3. Extract the tag version from each scope
4. Compare all tags — they MUST match

**Expected output**: `All 6 scopes use aihub-lib tag v1.2.3` or `MISMATCH: aihub_api uses v1.2.2, all others use v1.2.3`

### 1c. License audit

```bash
cd /home/user/aihub-core/<scope> && poetry run pip-licenses --format=table --order=license
```

Flag any packages with these license types:
- **GPL** (any version) — copyleft, incompatible with proprietary use
- **AGPL** — strong copyleft
- **Unknown** — license not detected, needs manual review

## Step 2: Audit Frontend Dependencies

```bash
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm outdated
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm audit
```

Report outdated count and any security advisories.

## Step 3: Summary Report

Produce a table:

| Scope | Dep Count | Outdated | Vulnerabilities | aihub-lib Version | License Flags |
|-------|-----------|----------|-----------------|-------------------|---------------|
| aihub_lib | 45 | 3 | 0 | v1.2.3 | None |
| aihub_api | 62 | 5 | 1 (moderate) | v1.2.3 | 1 unknown |
| frontend | 38 | 2 | 0 | N/A | None |

Include actionable recommendations:
- Critical vulnerabilities to fix immediately
- aihub-lib version mismatches to align
- Licenses requiring review

## Examples

- `/dependency-audit` — Full audit across all scopes
- `/dependency-audit aihub_api` — Audit only the API scope
- `/dependency-audit frontend` — Audit only frontend (pnpm)

## Troubleshooting

- **"pip-licenses not found"**: Install it with `poetry add --group dev pip-licenses` in the scope.
- **Poetry lock file out of date**: Run `poetry lock --no-update` to refresh without changing versions.
- **pnpm audit fails**: May require network access. Check proxy settings if behind a corporate firewall.

## Key Files

- Root Makefile license target: `make license-check`
- License generation script: `/home/user/aihub-core/generate-license.sh`

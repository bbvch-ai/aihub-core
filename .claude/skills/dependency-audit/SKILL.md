---
name: dependency-audit
description: Audit Python and Node.js dependencies for outdated packages,
  vulnerabilities, and version consistency across all scopes.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

# Dependency Health Audit

Audit all dependencies. Scope via `$ARGUMENTS` (scope name, "frontend", or "all").

## Python Scopes

For each scope (aihub_lib, aihub_agent, aihub_api, aihub_bot, aihub_pipeline, aihub_process):

### Outdated packages
```bash
cd /home/user/aihub-core/<scope> && poetry show --outdated
```

### aihub_lib version consistency
Read each scope's `pyproject.toml`, find the `aihub-lib` dependency tag, compare across all scopes. Flag any scope using a different tag.

### License audit
```bash
cd /home/user/aihub-core/<scope> && poetry run pip-licenses --format=table --order=license
```
Flag GPL, unknown, or copyleft licenses.

## Frontend

```bash
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm outdated
cd /home/user/aihub-core/aihub_web/aihub_web && pnpm audit
```

## Summary Report

Table with: scope, dep count, outdated, vulnerabilities, aihub-lib version. Flag license concerns and recommendations.

## Key Files

- Root Makefile license target: `make license-check`
- License generation script: `/home/user/aihub-core/generate-license.sh`

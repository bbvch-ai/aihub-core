---
name: lint
description: Format and lint code across all swiss-ai-hub scopes. Runs make pr-ready (ruff format + ruff check --fix + mdformat + yamlfix), fixes errors, and repeats until clean. Use when user says 'lint', 'format code', 'run pr-ready', 'fix formatting', 'ruff check', 'lint all scopes', or 'format and lint'. Do NOT use for running tests (use /test-scope) or full PR preparation (use /create-pr).
allowed-tools: Bash, Read, Edit
---

# Lint - Format and Lint All Scopes

Run `make pr-ready` from the repo root across the monorepo to format, lint, and fix code. Repeat until zero errors
remain.

The stop hook runs `make pr-ready` automatically at session end. Use this skill mid-session when you need to verify
linting is clean before proceeding (e.g., before running tests or reviewing code), or when the stop hook failed and you
need to diagnose and fix specific errors.

## What make pr-ready Does

The root `make pr-ready` runs these steps in sequence:

1. **Per-scope `make pr-ready`** for each Python scope (`packages/pipeline`, `packages/core`, `packages/agent`,
   `packages/process`, `packages/api`, `packages/sysadmin-api`, `packages/bot`, `packages/backup`):
   - `ruff format` — auto-format Python code
   - `ruff check --fix` — lint with auto-fix (rules: E pycodestyle, F pyflakes, UP pyupgrade, I isort)
2. **Frontend scopes** (`packages/web`, `packages/sysadmin-web`) run `pnpm lint` (ESLint) instead of ruff.
3. **`make generate-compose`, `check-env`, `generate-env-docs`, `license-check`** — regenerate and validate the compose
   files, env docs, and license headers
4. **`mdformat --number`** — format all tracked Markdown files (normalize headings, lists, tables)
5. **`yamlfix`** — format all tracked YAML files (except `pnpm-lock.yaml`)

## Steps

### 1. Run make pr-ready from Repo Root

```bash
make pr-ready
```

### 2. Review Output for Errors

Ruff auto-fixes most issues. Errors that remain after auto-fix require manual intervention:

- **Import errors** — missing dependency, run `uv sync --all-packages`
- **Unused imports/variables** — remove them
- **Unsafe fixes** — ruff flags these but won't auto-apply; review and fix manually
- **Syntax errors** — ruff can't auto-fix these; fix the Python syntax manually

### 3. Fix Errors and Re-run

Fix each error in the reported file. Then re-run:

```bash
make pr-ready
```

Repeat until the output shows zero errors across all scopes.

### 4. Run on Specific Scopes (Optional)

If only one scope needs fixing, target it directly:

```bash
make -C packages/core pr-ready
make -C packages/api pr-ready
make -C packages/web pr-ready
make -C packages/sysadmin-api pr-ready
make -C packages/backup pr-ready
```

## Ruff Configuration

Each scope's `pyproject.toml` configures ruff. Key settings:

- **Line length**: 120 characters
- **Target**: Python 3.13
- **Rules**: E (pycodestyle), F (pyflakes), UP (pyupgrade), I (isort)
- **Per-file ignores**: test files allow unused imports (F401) for fixtures

## Troubleshooting

| Problem                                        | Solution                                               |
| ---------------------------------------------- | ------------------------------------------------------ |
| `make pr-ready` fails with ModuleNotFoundError | Run `uv sync --all-packages` from workspace root       |
| mdformat fails on deleted file                 | Stage the deletion with `git rm` first                 |
| yamlfix changes too much                       | Check if the YAML file follows non-standard formatting |
| ESLint errors in packages/web                  | Run `pnpm lint --fix` from `packages/web/`             |

## Done When

- `make pr-ready` runs to completion with zero errors across all scopes

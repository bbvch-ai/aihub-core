---
name: create-pr
description: Validate and prepare code for a pull request across the aihub-core monorepo. Orchestrates committing, formatting, linting, testing, code review, version consistency, compose generation, and documentation sync. Use when user says 'create a PR', 'prepare pull request', 'get ready for PR', 'run pr-ready', 'validate my changes', 'prepare for review', 'pre-merge checks', 'is this ready to merge', or 'release validation'. Do NOT use for only running tests (use /test-scope), only reviewing code (use /review-diff), or only syncing docs (use /update-doc).
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Create PR - Pre-Pull Request Validation

Prepare code for a pull request by committing, formatting, linting, testing, reviewing, and validating all changes
across the monorepo. This skill does NOT create the actual PR -- it ensures everything is ready for one.

Delegates to specialized skills where available. Run all steps in order -- each depends on the previous.

## Steps

### 1. Commit Current Work

```bash
git status
git diff
git add <specific-files>
git commit -m "type(scope): Descriptive message"
```

- **Commit format**: `type(scope): subject` — types: `fix`, `feat`, `test`, `doc`, `chore`
- **Allowed scopes** (CI-enforced): `aihub`, `iac`, `ci-cd`, `agent-custom`, `agent-xp`, `avatar`, `bots`, `chat-xp`,
  `chat-backend`, `debt`, `dagster`, `confidence`, `deploy`, `ui`, `guards`, `rag`, `local`, `tracing`, `workflows`,
  `micro`
- Keep commits focused -- one logical change per commit
- Use imperative mood ("Add feature" not "Added feature")

### 2. Format and Lint All Scopes

Run `make pr-ready` from the repo root to format and lint all scopes at once:

```bash
make -C /home/joelbarmettler/projects/aihub/aihub-core pr-ready
```

This runs `ruff format` + `ruff check --fix` in every scope (`aihub_lib`, `aihub_agent`, `aihub_process`, `aihub_api`,
`aihub_bot`, `aihub_pipeline`). Fix any errors and re-run until clean.

If only specific scopes are affected, run individually:

```bash
make -C aihub_lib pr-ready
make -C aihub_api pr-ready
```

### 3. Run Tests via /test-scope

Delegate to the `/test-scope` skill for smart scoped testing. It auto-detects affected scopes from git diff, expands
downstream dependencies (e.g. `aihub_lib` change triggers all scopes), and runs `make test` in dependency order.

If `/test-scope` is not available, run manually in dependency order:

```bash
make -C aihub_lib test
make -C aihub_agent test
make -C aihub_pipeline test
make -C aihub_process test
make -C aihub_api test
make -C aihub_bot test
```

Every test must pass. Never disable or skip tests. Fix root causes, not symptoms.

### 4. Review Changes via /review-diff

Delegate to the `/review-diff` skill for a comprehensive code review of `git diff main...HEAD`. It checks architecture,
coding standards (type hints, Pydantic models, async I/O, fail-fast), security (OWASP top 10), and correctness.

Fix all critical and important issues found. Re-run `make pr-ready` and `make test` for any scopes modified during
fixes.

### 5. Version Consistency Check

Verify all scopes reference the same `aihub-core` (aihub_lib) version:

```bash
grep -r 'aihub-core' aihub_*/pyproject.toml | grep -E '(version|tag)'
```

All scopes must use the identical version. If any scope lags behind, update its `pyproject.toml` and run `uv lock` from
the workspace root.

### 6. Compose Generation Check

Verify Docker Compose files are up to date with templates:

```bash
make -C /home/joelbarmettler/projects/aihub/aihub-core generate-compose
git diff --stat
```

If `git diff` shows changes after regeneration, the templates were modified without regenerating. Commit the regenerated
files.

### 7. Update Documentation via /update-doc

Delegate to the `/update-doc` skill to sync documentation with code changes. It reviews affected READMEs, CLAUDE.md
files, and skills for staleness.

For significant architectural changes, also check whether an ADR is needed in `aihub_doc/arc42/decisions/` (see
`/document-decision`).

### 8. Git Cleanliness

```bash
git status
git log --oneline main..HEAD
```

Verify:

- No uncommitted changes remain
- All commits follow conventional format (`type(scope): subject`)
- Branch is pushed and up to date with remote

## Critical Rules

- **DO NOT** create the actual pull request -- only prepare for one
- **DO NOT** skip any failing test
- Fix the actual problem, not the symptom
- Commit fixes from review as separate commits (not amended into feature commits)

## Troubleshooting

| Problem                                  | Solution                                                                 |
| ---------------------------------------- | ------------------------------------------------------------------------ |
| `make pr-ready` fails with import errors | Run `uv sync --all-packages` from the workspace root                     |
| Tests fail with missing fixtures         | Check if scope depends on aihub_lib changes -- run aihub_lib tests first |
| Mypy strict mode errors                  | Add type annotations to all parameters, returns, and variables           |
| Version mismatch across scopes           | Update lagging scope's `pyproject.toml` and run `uv lock`                |
| Compose generation shows diff            | Run `make generate-compose` and commit the regenerated files             |

## Done When

- Changes committed with proper conventional commit messages
- `make pr-ready` runs clean across all scopes
- All tests pass (via `/test-scope`)
- Code review passed (via `/review-diff`)
- All scopes reference the same aihub-core version
- Docker Compose files match templates
- Documentation is current (via `/update-doc`)
- Git working tree is clean

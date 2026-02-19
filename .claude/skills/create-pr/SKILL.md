---
name: create-pr
description: Validate and prepare code for a pull request across the aihub-core monorepo. Orchestrates committing, formatting, linting, testing, code review, main sync, and documentation sync. Use when user says 'create a PR', 'prepare pull request', 'get ready for PR', 'validate my changes', 'prepare for review', 'pre-merge checks', 'is this ready to merge', or 'release validation'. Do NOT use for only running tests (use /test-scope), only reviewing code (use /review-diff), only syncing docs (use /update-doc), or only linting (use /lint).
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Create PR - Pre-Pull Request Validation

Prepare code for a pull request by orchestrating all validation steps across the monorepo. This skill does NOT create
the actual PR -- it ensures everything is ready for one.

Delegates to specialized skills for each concern. Run all steps in order.

## Steps

### 1. Commit Current Work

```bash
git status
git diff
git add <specific-files>
git commit -m "type(scope): Descriptive message"
```

- **Commit format**: `type(scope): subject` -- types: `fix`, `feat`, `test`, `doc`, `chore`
- **Allowed scopes** (CI-enforced): `aihub`, `iac`, `ci-cd`, `agent-custom`, `agent-xp`, `avatar`, `bots`, `chat-xp`,
  `chat-backend`, `debt`, `dagster`, `confidence`, `deploy`, `ui`, `guards`, `rag`, `local`, `tracing`, `workflows`,
  `micro`
- Keep commits focused -- one logical change per commit
- Use imperative mood ("Add feature" not "Added feature")

### 2. Sync with Main via /merge-main

Delegate to the `/merge-main` skill to ensure the branch is up to date with `origin/main`. It commits local work,
fetches main, reviews what changed, merges, and resolves conflicts (asking the user when unsure). This prevents merge
conflicts at PR time and ensures CI runs against the latest main.

### 3. Format and Lint via /lint

Delegate to the `/lint` skill. It runs `make pr-ready` from the repo root (ruff format + ruff check + mdformat + yamlfix
across all scopes), fixes errors, and repeats until clean.

### 4. Run Tests via /test-scope

Delegate to the `/test-scope` skill for smart scoped testing. It auto-detects affected scopes from git diff, expands
downstream dependencies (e.g. `aihub_lib` change triggers all scopes), and runs `make test` in dependency order.

Every test must pass. Never disable or skip tests. Fix root causes, not symptoms.

### 5. Review Changes via /review-diff

Delegate to the `/review-diff` skill for a comprehensive code review of `git diff main...HEAD`. It checks architecture,
coding standards (type hints, Pydantic models, async I/O, fail-fast), security (OWASP top 10), and correctness.

Fix all critical and important issues found. Re-run `/lint` and `/test-scope` for any scopes modified during fixes.

### 6. Update Documentation via /update-doc

Delegate to the `/update-doc` skill to sync documentation with code changes. It reviews affected READMEs, CLAUDE.md
files, and skills for staleness.

For significant architectural changes, also check whether an ADR is needed in `aihub_doc/arc42/decisions/` (see
`/document-decision`).

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
| Branch behind main                       | Run `/merge-main` to sync with origin/main before continuing             |

## Done When

- Changes committed with proper conventional commit messages
- Formatting and linting clean (via `/lint`)
- All tests pass (via `/test-scope`)
- Code review passed (via `/review-diff`)
- Branch is up to date with main (via `/merge-main`)
- Documentation is current (via `/update-doc`)

---
name: create-pr
description: "Validate and prepare code for a pull request: commit, format, lint,
  type-check, and test all affected scopes. Use when user says 'create a PR',
  'prepare pull request', 'get ready for PR', 'run pr-ready', 'validate my changes',
  or 'prepare for review'. Commits work, runs make pr-ready and make test in every
  scope, reviews diff against main, and updates docs."
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Create PR - Pre-Pull Request Validation

Prepare code for a pull request by committing, formatting, linting, testing, and reviewing all changes. This skill does
NOT create the actual PR -- it ensures everything is ready for one.

## Steps

### 1. Commit Current Work

```bash
git status
git diff
git add <specific-files>
git commit -m "type(scope): Descriptive message"
```

- **Commit format**: `type(scope): subject` (types: fix, feat, test, doc, chore)
- Keep commits focused -- one logical change per commit
- Use imperative mood ("Add feature" not "Added feature")

### 2. Format and Lint All Affected Scopes

Run `make pr-ready` in each scope. Fix errors immediately and re-run until clean.

```bash
# Run in each affected scope (always start with aihub_lib if modified)
cd aihub_lib && poetry shell && make pr-ready && exit
cd ../aihub_pipeline && poetry shell && make pr-ready && exit
cd ../aihub_agent && poetry shell && make pr-ready && exit
cd ../aihub_process && poetry shell && make pr-ready && exit
cd ../aihub_api && poetry shell && make pr-ready && exit
cd ../aihub_bot && poetry shell && make pr-ready && exit
cd ..
```

**Expected output**: No formatting errors, no lint warnings, no type check failures.

### 3. Run All Tests

Run `make test` in each scope. Every test must pass.

```bash
cd aihub_lib && poetry shell && make test && exit
cd ../aihub_pipeline && poetry shell && make test && exit
cd ../aihub_agent && poetry shell && make test && exit
cd ../aihub_process && poetry shell && make test && exit
cd ../aihub_api && poetry shell && make test && exit
cd ../aihub_bot && poetry shell && make test && exit
cd ..
```

- Read error messages carefully -- fix the root cause
- Never disable or skip tests
- Re-run until all green

### 4. Review Changes Against Main

```bash
git diff main...HEAD
```

**Inspection checklist**:
- Hunt for bugs: edge cases, null pointers, resource leaks, race conditions
- Enforce coding standards: "why" comments, docstrings on public APIs, type annotations, Pydantic over dicts, fail-fast error handling
- Respect architecture: code in the right scope, shared code in aihub_lib, no customer-specific info

### 5. Fix Issues Found

1. Fix each problem properly (not symptoms)
2. Re-run `make pr-ready` and `make test` for affected scopes
3. Verify fixes actually solved the problems

### 6. Final Check

1. Run `git status` -- inventory everything touched
2. Run `git diff` -- final read-through
3. Confirm: "Does this solve exactly what the task asked for?"

### 7. Update Documentation

Follow the `/update-doc` skill to sync documentation with code changes.

## Critical Rules

- **DO NOT** create the actual pull request -- only prepare for one
- **DO NOT** skip any failing test -- every single one must pass
- Fix the actual problem, not the symptom
- Follow typing and documentation standards
- Update documentation when changes affect it

## Examples

**Typical invocation**: `/create-pr` after finishing a feature branch

**Expected workflow**:
1. User completes feature work on a branch
2. Runs `/create-pr`
3. Skill commits, formats, tests, reviews all changes
4. User then manually creates the PR or asks separately

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `make pr-ready` fails with import errors | Run `poetry install` in the scope first |
| Tests fail with missing fixtures | Check if scope depends on aihub_lib changes -- run aihub_lib tests first |
| MyPy strict mode errors | Add type annotations to all parameters, returns, and variables |
| `poetry shell` not found | Ensure Poetry is installed and you are in the correct scope directory |

## Done When

- Changes committed with proper semantic commit messages
- Every `make pr-ready` runs clean in all affected scopes
- Every `make test` shows all green
- Git diff reviewed and clean
- Code does exactly what was asked
- Documentation is updated

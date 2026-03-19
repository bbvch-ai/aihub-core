---
name: merge-main
description: Sync the current feature branch with main by committing local work, fetching and merging origin/main, and resolving conflicts. Use when user says 'merge main', 'update from main', 'sync with main', 'pull main into branch', 'branch is behind main', 'rebase on main', or 'update my branch'. Do NOT use for creating PRs (use /create-pr), reviewing code (use /review-diff), or running tests (use /test-scope).
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Merge Main - Sync Feature Branch with Main

Bring the current feature branch up to date with `origin/main` by committing local work, understanding what changed on
main, merging, and resolving any conflicts. This ensures the branch is ready for a clean PR.

## Steps

### 1. Commit Current Work

Ensure all local changes are committed before merging. Uncommitted changes will cause merge failures.

```bash
git status
git diff --stat
```

If there are uncommitted changes:

```bash
git add <specific-files>
git commit -m "type(scope): Descriptive message"
```

- **Commit format**: `type(scope): subject` — types: `fix`, `feat`, `test`, `doc`, `chore`
- Do NOT commit with a generic "WIP" message — write a proper conventional commit

### 2. Fetch Latest Main

```bash
git fetch origin main
```

Check how far behind the branch is:

```bash
git log --oneline HEAD..origin/main | wc -l
git log --oneline origin/main..HEAD | wc -l
```

Report to the user: "Your branch is X commits behind main and Y commits ahead."

If the branch is already up to date (0 commits behind), stop here and inform the user.

### 3. Understand What Changed on Main

Review the commit history on main since the branch diverged:

```bash
git log --oneline HEAD..origin/main
```

For a deeper understanding, look at which files were changed on main:

```bash
git diff --stat HEAD...origin/main
```

Identify files that were changed on **both** main and this branch (potential conflict zones):

```bash
git diff --name-only HEAD...origin/main > /tmp/main_changes.txt
git diff --name-only origin/main...HEAD > /tmp/branch_changes.txt
comm -12 <(sort /tmp/main_changes.txt) <(sort /tmp/branch_changes.txt)
```

Summarize for the user:

- How many commits landed on main
- Which scopes were affected on main (packages/core, packages/api, etc.)
- Which files overlap between main and this branch (conflict risk areas)

### 4. Merge Main into Branch

```bash
git merge origin/main
```

**If the merge completes cleanly** (no conflicts): proceed to Step 6.

**If there are conflicts**: proceed to Step 5.

### 5. Resolve Conflicts

List all conflicted files:

```bash
git diff --name-only --diff-filter=U
```

For each conflicted file:

1. **Read the file** to understand both sides of the conflict
2. **Read the main-side changes** for context: `git log --oneline -5 origin/main -- <file>`
3. **Decide resolution strategy**:

**Resolve yourself** when:

- The conflict is in auto-generated files (`uv.lock`, `docker-compose.*.yml`) — accept main's version and regenerate
- The conflict is purely additive (both sides added different things to a list, import block, config)
- The conflict is in files you didn't intentionally modify (formatting, linting changes)
- The conflict is in `pyproject.toml` dependency sections — merge both sets of deps, then run `uv lock`

**Ask the user** when:

- Both sides made substantive changes to the same function or class
- The conflict involves architectural decisions or design choices
- You're unsure which side's intent should take priority
- The conflict is in business logic or test assertions

After resolving each file:

```bash
git add <resolved-file>
```

After all conflicts are resolved:

```bash
git commit
```

Use the default merge commit message — do NOT amend it.

### 6. Post-Merge Validation

After a successful merge, verify the codebase is healthy:

```bash
uv sync --all-packages
```

Run `make pr-ready` from the repo root to ensure formatting and linting pass after merge:

```bash
make -C /home/joelbarmettler/projects/aihub/aihub-core pr-ready
```

If `uv.lock` was conflicted or dependencies changed on main, regenerate it:

```bash
uv lock
```

If Docker Compose templates were touched on main, regenerate:

```bash
make -C /home/joelbarmettler/projects/aihub/aihub-core generate-compose
```

Commit any post-merge fixups:

```bash
git add <fixed-files>
git commit -m "chore(swiss-ai-hub): Post-merge fixups after syncing with main"
```

### 7. Verify with /review-diff

Delegate to the `/review-diff` skill to review the full diff between the updated branch and main. This catches any merge
mistakes where the wrong side of a conflict was kept or where the merge introduced inconsistencies.

## Critical Rules

- **NEVER force-push** after merging — the merge commit is permanent
- **NEVER use `git rebase`** on a branch that has been pushed — use merge instead
- **NEVER resolve a conflict by silently dropping one side** — if both sides made real changes, ask the user
- **Commit before merging** — uncommitted work will be lost or cause merge failures
- Always use the default merge commit message

## Troubleshooting

| Problem                         | Solution                                                                       |
| ------------------------------- | ------------------------------------------------------------------------------ |
| `uv.lock` conflict              | Accept either side, then run `uv lock` to regenerate                           |
| `docker-compose.*.yml` conflict | Accept either side, then run `make generate-compose` to regenerate             |
| Merge breaks imports            | Run `uv sync --all-packages` to reinstall deps, then `make pr-ready`           |
| Tests fail after merge          | Run `/test-scope` to identify which scope broke, fix, and commit               |
| Merge was a mistake             | Ask the user before running `git merge --abort` (only works before committing) |

## Done When

- All commits on main are now in the feature branch
- No merge conflicts remain
- `make pr-ready` passes
- Post-merge fixups are committed

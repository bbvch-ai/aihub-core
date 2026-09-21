---
name: create-pr
description: Validate and prepare code for a pull request across the swiss-ai-hub monorepo. Orchestrates committing, formatting, linting, testing, code review, main sync, documentation sync, and the SonarCloud findings check after the branch is pushed. Use when user says 'create a PR', 'prepare pull request', 'get ready for PR', 'validate my changes', 'prepare for review', 'pre-merge checks', 'is this ready to merge', 'release validation', or 'check sonar issues on my PR'. Do NOT use for only running tests (use /test-scope), only reviewing code (use /review-diff), only syncing docs (use /update-doc), or only linting (use /lint).
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Create PR - Pre-Pull Request Validation

Prepare code for a pull request by orchestrating all validation steps across the monorepo. This skill does NOT create
the actual PR -- it ensures everything is ready for one.

Delegates to specialized skills for each concern. Run steps 1-6 in order before the PR exists. Step 7 (SonarCloud) runs
**after** the branch is pushed, because SonarCloud only analyses what CI has scanned -- come back to it once the branch
is up, whether this skill pushed it or the user did.

## Steps

### 1. Commit Current Work

```bash
git status
git diff
git add <specific-files>
git commit -m "type(scope): Descriptive message"
```

- **Commit format**: `type(scope): subject` -- types: `fix`, `feat`, `test`, `doc`, `chore`
- **Allowed scopes** (CI-enforced): `swiss-ai-hub`, `iac`, `ci-cd`, `bots`, `dagster`, `deploy`, `ui`, `guards`, `rag`,
  `tracing`, `workflows`
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
downstream dependencies (e.g. `packages/core` change triggers all scopes), and runs `make test` in dependency order.

Every test must pass. Never disable or skip tests. Fix root causes, not symptoms.

### 5. Review Changes via /review-diff

Delegate to the `/review-diff` skill for a comprehensive code review of `git diff main...HEAD`. It checks architecture,
coding standards (type hints, Pydantic models, async I/O, fail-fast), security (OWASP top 10), and correctness.

Fix all critical and important issues found. Re-run `/lint` and `/test-scope` for any scopes modified during fixes.

### 6. Update Documentation via /update-doc

Delegate to the `/update-doc` skill to sync documentation with code changes. It reviews affected READMEs, CLAUDE.md
files, and skills for staleness.

For significant architectural changes, also check whether an ADR is needed in `docs/arc42/decisions/` (see
`/document-decision`).

### 7. Check SonarCloud After the Branch Is Pushed

CI scans every package as its own SonarCloud project, so a clean local run is not a clean Sonar run. Once the branch is
pushed and the Sonar job has finished, pull the findings instead of waiting for a reviewer to relay them.

**Requires the `sonarqube` MCP server.** It needs `SONARQUBE_TOKEN` in `.env` (see `.claude/README.md` -> "MCP Server
Environment Keys"). If the server is not connected, tell the user once and skip this step -- do not install it and do
not guess at findings.

```bash
gh pr checks              # confirm the Sonar job finished; analysis runs AFTER CI
```

Then query only the packages your diff touched. Project keys live in `packages/*/sonar-project.properties`:

| Package                 | Project key               | Package                 | Project key                 |
| ----------------------- | ------------------------- | ----------------------- | --------------------------- |
| `packages/core`         | `aihub-core_lib-core`     | `packages/api`          | `aihub-core_api-core`       |
| `packages/agent`        | `aihub-core_agents-core`  | `packages/pipeline`     | `aihub-core_pipelines-core` |
| `packages/process`      | `aihub-core_process-core` | `packages/bot`          | `aihub-core_bot-core`       |
| `packages/backup`       | `aihub-core_backup-core`  | `packages/web`          | `aihub-core_aihub-web`      |
| `packages/sysadmin-api` | `aihub-core_sysadmin-api` | `packages/sysadmin-web` | `aihub-core_sysadmin-web`   |

Use `search_sonar_issues_in_projects` with the **PR number** as `pullRequest`, and `get_project_quality_gate_status` for
the gate. Two gotchas: `ps` must be a **number**, not a string, and `search_my_sonarqube_projects` matches the display
name ("Agents Core"), not the key -- take keys from the table above rather than discovering them.

**What to fix automatically.** Only findings whose fix is local, obvious, and cannot change behaviour:

- unused imports, variables or parameters
- redundant casts, redundant `else` after `return`
- duplicated string literals -> extract a constant
- cognitive complexity over the limit -> extract a helper (when the extraction is mechanical)
- naming convention violations

Commit these as a separate `fix(<scope>): Address SonarCloud findings` commit and push.

**What to escalate instead.** Report to the user with the rule key, file, line and the risk -- do not touch:

- anything altering control flow or error handling
- security, auth or crypto findings
- changes to a public signature or an exported type
- anything needing a design decision, or arguably a false positive

Some findings are deliberately left open (`S112` on the MinerU loader unwrap, for one). Check `git log` and existing
Sonar comments before "fixing" one.

**Always report back.** Tell the user what Sonar found, what you fixed, and what you left -- including when the answer
is "nothing found". Never fix a Sonar finding silently.

## Critical Rules

- **DO NOT** create the actual pull request -- only prepare for one
- **DO NOT** fix a Sonar finding silently -- always report what was fixed
- **DO NOT** skip any failing test
- Fix the actual problem, not the symptom
- Commit fixes from review as separate commits (not amended into feature commits)

## Troubleshooting

| Problem                                  | Solution                                                                                   |
| ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| `make pr-ready` fails with import errors | Run `uv sync --all-packages` from the workspace root                                       |
| Tests fail with missing fixtures         | Check if scope depends on packages/core changes -- run packages/core tests first           |
| Mypy strict mode errors                  | Add type annotations to all parameters, returns, and variables                             |
| Branch behind main                       | Run `/merge-main` to sync with origin/main before continuing                               |
| `sonarqube` MCP not connected            | `SONARQUBE_TOKEN` missing or expired in `.env` (30-day default) -- see `.claude/README.md` |
| Sonar returns no issues for the PR       | Analysis runs after CI; check `gh pr checks` and retry once the Sonar job is green         |

## Done When

- Changes committed with proper conventional commit messages
- Formatting and linting clean (via `/lint`)
- All tests pass (via `/test-scope`)
- Code review passed (via `/review-diff`)
- Branch is up to date with main (via `/merge-main`)
- Documentation is current (via `/update-doc`)
- SonarCloud findings on the pushed branch triaged: trivial ones fixed and pushed, the rest reported to the user

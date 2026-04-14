---
name: implement-feedback-from-pr
description: Implement review feedback from a pull request. Fetches PR comments, distinguishes human from bot feedback, prioritizes and implements changes, then validates. Use when user says 'implement PR feedback', 'address review comments', 'fix PR review', 'apply PR suggestions', 'handle reviewer feedback', or 'implement changes from review'. Takes a PR number as argument. Do NOT use for pre-PR code review (use /review-diff) or PR creation (use /create-pr).
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Implement PR Feedback - Turn Reviews into Improvements

Implement review feedback from PR \$ARGUMENTS in the `bbvch-ai/aihub-core` monorepo.

## Step 1: Fetch Unresolved Feedback Only

Use the GitHub GraphQL API via `gh api graphql` to fetch **only unresolved, non-outdated** review threads:

```bash
gh api graphql -f query='
{
  repository(owner: "bbvch-ai", name: "aihub-core") {
    pullRequest(number: $PR_NUMBER) {
      reviewThreads(first: 50) {
        nodes {
          isResolved
          isOutdated
          comments(first: 10) {
            nodes {
              body
              path
              line
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}'
```

Filter to only threads where `isResolved: false` and `isOutdated: false`. Resolved and outdated threads have already
been addressed — skip them entirely.

Also fetch CI status and changed files for scope detection:

```bash
gh pr checks $PR_NUMBER -R bbvch-ai/aihub-core
gh pr view $PR_NUMBER -R bbvch-ai/aihub-core --json files
```

## Step 2: Triage Feedback

### Human Comments (TOP PRIORITY)

Implement all **unresolved** human reviewer feedback. Read the referenced file before making changes. Skip resolved
threads — they have already been addressed in previous commits.

### Bot Feedback (EVALUATE CRITICALLY)

This repo's CI pipeline (`.github/workflows/analyze-test-pr.yml`) runs three bot checks:

- **`test-modules`** — pytest across scopes. Failures here are real — fix the code.

- **`pytest-coverage-comment`** — coverage delta. Add tests only if the uncovered code is meaningful.

- **`sonarcloud-scan`** — scans three SonarCloud projects:

  - `swiss-ai-hub_lib-core` (packages/core)
  - `swiss-ai-hub_api-core` (packages/api)
  - `swiss-ai-hub_agents-core` (packages/agent)

  SonarCloud bugs and vulnerabilities: almost always fix. Code smells: fix if straightforward. Security hotspots:
  evaluate case-by-case.

## Step 3: Identify Affected Scopes

Use the file list from Step 1 (`get_files`) to determine which monorepo scopes need testing. Map changed file paths to
scopes: `packages/core/` → packages/core, `packages/api/` → packages/api, `packages/agent/` → packages/agent,
`packages/pipeline/` → packages/pipeline, `packages/process/` → packages/process, `packages/bot/` → packages/bot,
`packages/web/` → packages/web.

## Step 4: Implement Changes

For each comment, read the referenced file, make the change, and move to the next. Work through human comments first,
then bot findings.

## Step 5: Validate

After all changes are implemented:

```bash
# Lint all affected scopes
make -C /home/joelbarmettler/projects/aihub/aihub-core pr-ready

# Run tests in affected scopes (or delegate to /test-scope)
make -C packages/core test    # if packages/core was affected
make -C packages/api test    # if packages/api was affected
```

## Troubleshooting

| Problem                             | Solution                                                              |
| ----------------------------------- | --------------------------------------------------------------------- |
| MCP `get` returns no PR             | Verify PR number: `gh pr list`                                        |
| Inline comments not visible         | Use `get_review_comments` method (not `get_comments`)                 |
| SonarCloud findings unclear         | Check the SonarCloud link in the bot comment for detailed explanation |
| `make pr-ready` fails after changes | Fix lint errors introduced by your fixes, re-run                      |
| Tests fail in unrelated scope       | Check if `packages/core` changes broke a downstream scope             |

## Done When

- Every human comment addressed or responded to
- All critical SonarCloud and test-module findings resolved
- `make pr-ready` runs clean from repo root
- `make test` passes in all affected scopes

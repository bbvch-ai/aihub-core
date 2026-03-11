---
name: implement-feedback-from-pr
description: Implement review feedback from a pull request. Fetches PR comments, distinguishes human from bot feedback, prioritizes and implements changes, then validates. Use when user says 'implement PR feedback', 'address review comments', 'fix PR review', 'apply PR suggestions', 'handle reviewer feedback', or 'implement changes from review'. Takes a PR number as argument. Do NOT use for pre-PR code review (use /review-diff) or PR creation (use /create-pr).
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Implement PR Feedback - Turn Reviews into Improvements

Implement review feedback from PR \$ARGUMENTS in the `bbvch-ai/aihub-core` monorepo.

## Step 1: Fetch All Feedback

Fetch PR data using the `gh` CLI. **Only act on unresolved comments** — skip anything already resolved by the author or
reviewer.

1. **PR overview**: `gh pr view $PR_NUMBER --repo bbvch-ai/aihub-core --json title,body,author,baseRefName,headRefName`
2. **Review threads (unresolved only)**: Use the GraphQL API to fetch review threads filtered to unresolved. Write the
   query to a temp file first (to avoid `$` escaping issues in the Bash tool), then execute:
   ```bash
   cat > /tmp/pr-threads.graphql << 'GRAPHQL'
   query($owner: String!, $repo: String!, $pr: Int!) {
     repository(owner: $owner, name: $repo) {
       pullRequest(number: $pr) {
         reviewThreads(first: 100) {
           nodes {
             isResolved
             isOutdated
             comments(first: 20) {
               nodes { author { login } body path line createdAt }
             }
           }
         }
       }
     }
   }
   GRAPHQL
   gh api graphql -f "query=$(cat /tmp/pr-threads.graphql)" \
     -f owner=bbvch-ai -f repo=aihub-core -F pr=$PR_NUMBER \
     | jq '[.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)]'
   ```
   This returns all unresolved review threads.
3. **Conversation comments**: `gh pr view $PR_NUMBER --repo bbvch-ai/aihub-core --json comments`
4. **CI status**: `gh pr checks $PR_NUMBER --repo bbvch-ai/aihub-core`
5. **Changed files**: `gh pr diff $PR_NUMBER --repo bbvch-ai/aihub-core --name-only`

## Step 2: Triage Feedback

### Human Comments (TOP PRIORITY)

Implement all **unresolved** human reviewer feedback first. Read the referenced file before making changes. If a review
thread is marked as resolved, the author has already addressed it — do not re-implement.

### Bot Feedback (EVALUATE CRITICALLY)

This repo's CI pipeline (`.github/workflows/analyze-test-pr.yml`) runs three bot checks:

- **`test-modules`** — pytest across scopes. Failures here are real — fix the code.

- **`pytest-coverage-comment`** — coverage delta. Add tests only if the uncovered code is meaningful.

- **`sonarcloud-scan`** — scans three SonarCloud projects:

  - `aihub-core_lib-core` (aihub_lib)
  - `aihub-core_api-core` (aihub_api)
  - `aihub-core_agents-core` (aihub_agent)

  SonarCloud bugs and vulnerabilities: almost always fix. Code smells: fix if straightforward. Security hotspots:
  evaluate case-by-case.

## Step 3: Identify Affected Scopes

Use the file list from Step 1 (`get_files`) to determine which monorepo scopes need testing. Map changed file paths to
scopes: `aihub_lib/` → aihub_lib, `aihub_api/` → aihub_api, `aihub_agent/` → aihub_agent, `aihub_pipeline/` →
aihub_pipeline, `aihub_process/` → aihub_process, `aihub_bot/` → aihub_bot, `aihub_web/` → aihub_web.

## Step 4: Implement Changes

For each comment, read the referenced file, make the change, and move to the next. Work through human comments first,
then bot findings.

## Step 5: Validate

After all changes are implemented:

```bash
# Lint all affected scopes
make pr-ready

# Run tests in affected scopes (or delegate to /test-scope)
make -C aihub_lib test    # if aihub_lib was affected
make -C aihub_api test    # if aihub_api was affected
```

## Troubleshooting

| Problem                             | Solution                                                              |
| ----------------------------------- | --------------------------------------------------------------------- |
| MCP `get` returns no PR             | Verify PR number: `gh pr list`                                        |
| Inline comments not visible         | Use `get_review_comments` method (not `get_comments`)                 |
| SonarCloud findings unclear         | Check the SonarCloud link in the bot comment for detailed explanation |
| `make pr-ready` fails after changes | Fix lint errors introduced by your fixes, re-run                      |
| Tests fail in unrelated scope       | Check if `aihub_lib` changes broke a downstream scope                 |

## Done When

- Every human comment addressed or responded to
- All critical SonarCloud and test-module findings resolved
- `make pr-ready` runs clean from repo root
- `make test` passes in all affected scopes

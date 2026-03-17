---
name: splice-issue
description: "Break a large GitHub issue from bbvch-ai/aihub-core into self-contained, independently mergeable sub-issues with blocked-by dependency relationships. Use when user says 'splice this issue', 'split issue into sub-issues', 'break down issue #X', 'create sub-issues for #X', 'slice this issue', or 'decompose this issue'. Takes an issue number or URL as argument. Do NOT use for implementation planning within a single issue (use /plan-issue), creating PRs (use /create-pr), or fetching issue details without splicing (use gh issue view)."
allowed-tools: Bash, Read, Grep, Glob, Agent
---

# Splice Issue — Break Parent Issues into Sub-Issues

Break a parent issue into self-contained, independently mergeable sub-issues on GitHub.

## Before You Start

Read the memory file for issue structure conventions:
`/home/thomas/.claude/projects/-home-thomas-Projects-aihub-core/memory/feedback_issue_structure.md`

Review existing spliced issues for structure patterns:

```bash
gh api graphql -f query='{ repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: 919) { subIssues(first: 15) { nodes { number title state } } } } }'
```

## Step 1: Fetch the Parent Issue

```bash
gh issue view $ISSUE_NUMBER -R bbvch-ai/aihub-core --json title,body,labels,milestone,assignees
```

Also fetch any existing sub-issues — the user may have started splicing already:

```bash
gh api graphql -f query='{ repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $ISSUE_NUMBER) { id subIssues(first: 50) { nodes { number title state } } } } }'
```

Also fetch discussion comments for additional context and decisions:

```bash
gh issue view $ISSUE_NUMBER -R bbvch-ai/aihub-core --json comments --jq '.comments[].body'
```

## Step 2: Analyze and Propose the Breakdown

Identify logical, self-contained units of work from the issue body. Each sub-issue must be:

- **Independently mergeable**: Can be implemented and merged on its own
- **Self-contained**: Has clear acceptance criteria that don't require other sub-issues to validate
- **Appropriately scoped**: Small enough to be a single PR, large enough to be meaningful

Present the proposed breakdown to the user BEFORE creating any issues. Include:

- Title for each sub-issue
- Draft acceptance criteria
- Dependency relationships (which issues block which)
- What gets removed from the parent issue

Wait for user confirmation before proceeding.

## Step 3: Create Sub-Issues

For each approved sub-issue, create it with matching metadata from the parent:

```bash
gh issue create -R bbvch-ai/aihub-core \
  --title "Sub-issue title" \
  --body "$(cat <<'EOF'
Parent: #$ISSUE_NUMBER

Acceptance Criteria:

- [ ] Criterion 1
- [ ] Criterion 2
EOF
)" \
  --label "$PARENT_LABEL" \
  --milestone "$PARENT_MILESTONE" \
  --assignee "$PARENT_ASSIGNEE"
```

**Metadata inheritance rules:**

- Copy `--label` (version label: major/minor/patch) from parent
- Copy `--milestone` from parent
- Copy `--assignee` from parent
- Body starts with `Parent: #$ISSUE_NUMBER`

## Step 4: Link as Sub-Issues

Get the parent issue node ID and each child's node ID, then link them:

```bash
PARENT_ID=$(gh api graphql -f query='{ repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $ISSUE_NUMBER) { id } } }' -q '.data.repository.issue.id')

CHILD_ID=$(gh api graphql -f query='{ repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $CHILD_NUMBER) { id } } }' -q '.data.repository.issue.id')

gh api graphql -f query="mutation { addSubIssue(input: { issueId: \"$PARENT_ID\", subIssueId: \"$CHILD_ID\" }) { issue { id } } }"
```

## Step 5: Set Blocked-By Dependencies

For issues that depend on each other, use the `addBlockedBy` mutation:

```bash
ISSUE_ID=$(gh api graphql -f query='{ repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $BLOCKED_ISSUE) { id } } }' -q '.data.repository.issue.id')
BLOCKING_ID=$(gh api graphql -f query='{ repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $BLOCKING_ISSUE) { id } } }' -q '.data.repository.issue.id')

gh api graphql -f query="mutation { addBlockedBy(input: { issueId: \"$ISSUE_ID\", blockingIssueId: \"$BLOCKING_ID\" }) { issue { id } } }"
```

**Do NOT use `addSubIssue` for dependency relationships.** Sub-issue = part of the work. Blocked-by = must be done
first.

## Step 6: Clean Up the Parent Issue

After all sub-issues are created and linked:

1. **Remove acceptance criteria** from the parent issue body. AC lives only on leaf issues (issues with no children).
2. **Keep context sections** (background, design decisions, discussion history) — these provide valuable context for
   anyone working on the sub-issues.
3. **Do NOT create separate documentation sub-issues.** Documentation is part of the Definition of Done for every issue.

## Step 7: Present Summary

Show the user the final structure with dependency graph:

```
#919 Parent Issue (no AC, context only)
├── #954 Foundational issue (no deps)
│   ↓ blocks
├── #956 Mid-layer issue
│   ↓ blocks
├── #955 Leaf issue (blocked by #956)
└── #963 Leaf issue (blocked by #956)
```

## Common Mistakes

1. **Creating documentation as a separate sub-issue.** Documentation is DoD for every issue — never split it out.
2. **Leaving acceptance criteria on the parent issue.** Once a parent has sub-issues, remove its AC. The parent is done
   when all children are done.
3. **Using `addSubIssue` for dependencies.** Sub-issue means "part of this work." Use `addBlockedBy` for "must be done
   before."
4. **Forgetting to inherit metadata.** Every sub-issue must have the same label (major/minor/patch), milestone, and
   assignee as the parent.
5. **Creating issues before getting user confirmation.** Always present the proposed breakdown and wait for approval.

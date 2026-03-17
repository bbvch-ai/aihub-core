---
name: splice-issue
description: "Break a large GitHub issue from bbvch-ai/aihub-core into self-contained, independently mergeable sub-issues with blocked-by dependency relationships. Use when user says 'splice this issue', 'split issue into sub-issues', 'break down issue #X', 'create sub-issues for #X', 'slice this issue', or 'decompose this issue'. Takes an issue number or URL as argument. Do NOT use for implementation planning within a single issue (use /plan-issue), creating PRs (use /create-pr), or fetching issue details without splicing (use gh issue view)."
allowed-tools: Bash, Read, Grep, Glob
---

# Splice Issue — Break Parent Issues into Sub-Issues

Break a parent issue into self-contained, independently mergeable sub-issues on GitHub.

Parse the issue number from `$ARGUMENTS` (accepts `#123`, `123`, or a full GitHub URL).

## Before You Start

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
gh api graphql -F number=$ISSUE_NUMBER -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") {
      issue(number: $number) { id subIssues(first: 50) { nodes { number title state } } }
    }
  }'
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

**Acceptance criteria rules:**

- AC describes *what* should work, not *how* it's implemented
- No endpoint paths, class names, specific validation mechanisms, or other implementation details that could change
- Use behavior-oriented language ("users can switch tenants") not implementation-specific language ("composable exists
  for managing selected tenant with localStorage persistence")
- Implementation details belong in a separate "Implementation Proposal" section in the body

## Step 4: Link as Sub-Issues

Get the parent issue node ID and each child's node ID, then link them:

```bash
PARENT_ID=$(gh api graphql -F number=$ISSUE_NUMBER -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $number) { id } }
  }' -q '.data.repository.issue.id')

CHILD_ID=$(gh api graphql -F number=$CHILD_NUMBER -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $number) { id } }
  }' -q '.data.repository.issue.id')

gh api graphql -f query="mutation { addSubIssue(input: { issueId: \"$PARENT_ID\", subIssueId: \"$CHILD_ID\" }) { issue { id } } }"
```

## Step 5: Inherit Relationships from Parent

The parent's blocked-by and blocking relationships must transfer to the children. Fetch both:

```bash
gh api graphql -F number=$ISSUE_NUMBER -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") {
      issue(number: $number) {
        blockedBy(first: 10) { nodes { number id } }
        blocking(first: 10) { nodes { number id } }
      }
    }
  }'
```

- **blocked-by**: If parent is blocked by X, each child must also be blocked by X (the children can't start until X is
  done).
- **blocking**: If Y is blocked by parent, Y must now be blocked by each child (Y can't start until all children are
  done).

Apply the no-redundancy rule: skip if already covered transitively.

## Step 6: Set Blocked-By Dependencies Between Children

For children that depend on each other, use the `addBlockedBy` mutation:

```bash
ISSUE_ID=$(gh api graphql -F number=$BLOCKED_ISSUE -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $number) { id } }
  }' -q '.data.repository.issue.id')

BLOCKING_ID=$(gh api graphql -F number=$BLOCKING_ISSUE -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") { issue(number: $number) { id } }
  }' -q '.data.repository.issue.id')

gh api graphql -f query="mutation { addBlockedBy(input: { issueId: \"$ISSUE_ID\", blockingIssueId: \"$BLOCKING_ID\" }) { issue { id } } }"
```

**Do NOT use `addSubIssue` for dependency relationships.** Sub-issue = part of the work. Blocked-by = must be done
first.

**No redundant blocked-by relationships.** Before adding a blocked-by link, check the existing blocked-by chain. If the
blocking issue is already reachable transitively (e.g., A blocked by B, B blocked by C — don't also add A blocked by C),
skip it. Check with:

```bash
gh api graphql -F number=$ISSUE_NUMBER -f query='
  query($number: Int!) {
    repository(owner: "bbvch-ai", name: "aihub-core") {
      issue(number: $number) {
        blockedBy(first: 10) {
          nodes { number title blockedBy(first: 10) { nodes { number title } } }
        }
      }
    }
  }'
```

## Step 7: Copy Project Board Priorities to Children

Fetch the parent's project board field values (Priority, etc.) and copy them to each child issue. The parent may be on
multiple project boards — copy priorities from all of them.

```bash
# Get parent's project items with priority values
gh api graphql -f query='
{
  node(id: "PARENT_NODE_ID") {
    ... on Issue {
      projectItems(first: 10) {
        nodes {
          id
          project { number title id }
          fieldValues(first: 20) {
            nodes {
              ... on ProjectV2ItemFieldSingleSelectValue {
                field { ... on ProjectV2SingleSelectField { name id } }
                name
                optionId
              }
            }
          }
        }
      }
    }
  }
}'

# For each child, get its project item IDs and set the same Priority values
gh api graphql -f query="
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: \"PROJECT_ID\"
    itemId: \"CHILD_ITEM_ID\"
    fieldId: \"PRIORITY_FIELD_ID\"
    value: { singleSelectOptionId: \"PRIORITY_OPTION_ID\" }
  }) { projectV2Item { id } }
}"
```

## Step 8: Clean Up the Parent Issue

After all sub-issues are created and linked:

1. **Remove acceptance criteria** from the parent issue body. AC lives only on leaf issues (issues with no children).
2. **Keep context sections** (background, design decisions, discussion history) — these provide valuable context for
   anyone working on the sub-issues.
3. **Do NOT create separate documentation sub-issues.** Documentation is part of the Definition of Done for every issue.

## Step 9: Present Summary

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

Wait for the user to explicitly confirm that all sub-issues are correct and complete before proceeding. Do NOT close the
parent until the user says they are happy with the breakdown.

## Step 10: Close the Parent Issue

Only after the user has confirmed all sub-issues are correct, close the parent issue. The work now lives in the children
— the parent is just a container.

```bash
gh issue close $ISSUE_NUMBER -R bbvch-ai/aihub-core -r "not planned" -c "Spliced into sub-issues. Work continues in child issues."
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
6. **Adding redundant blocked-by relationships.** If A is blocked by B, and B is blocked by C, do NOT also add A blocked
   by C. Check the transitive chain first.
7. **Not copying project board priorities.** Every sub-issue must inherit the parent's Priority field values from all
   project boards.
8. **Putting implementation details in acceptance criteria.** AC describes behavior, not implementation. Put
   implementation details in a separate "Implementation Proposal" section.
9. **Not inheriting blocked-by/blocking relationships.** Children must inherit the parent's blocked-by (prerequisites)
   and blocking (dependents) relationships. Otherwise the dependency graph breaks when the parent is closed.

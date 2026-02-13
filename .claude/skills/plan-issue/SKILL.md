---
name: plan-issue
description: >-
  Fetch a GitHub issue and create a detailed implementation plan. Reads the issue, explores relevant
  code, identifies affected files, and proposes a step-by-step approach. Use when user says 'plan
  this issue', 'how should I implement issue #X', 'plan implementation', 'break down this issue',
  'fetch issue and plan', 'what needs to change for #X', or 'implementation strategy for issue'.
  Takes an issue number as argument.
allowed-tools: Bash, Read, Grep, Glob
---

# Plan Issue - GitHub Issue to Implementation Plan

Fetch a GitHub issue and produce a detailed implementation plan with affected files, approach, and risks.

## Step 1: Fetch the Issue

```bash
gh issue view $ARGUMENTS -c
```

Read the full issue description and all comments. Extract:
- **Goal**: What needs to be achieved
- **Constraints**: Any requirements or limitations mentioned
- **Context**: Related issues, PRs, or discussions referenced

## Step 2: Explore Relevant Code

Based on the issue, identify which scopes and files are involved:

1. Read the relevant scope `CLAUDE.md` files to understand architecture
2. Search for related code using `Grep` and `Glob`
3. Read the key files that will need modification
4. Check for existing patterns that should be followed

## Step 3: Check Existing ADRs

Read ADRs in `aihub_doc/arc42/decisions/` for decisions that affect the approach.

## Step 4: Create the Plan

### Format

```
## Issue Summary
One-sentence summary of what needs to be done.

## Affected Scopes
- `scope_name` — what changes here and why

## Implementation Steps

### 1. [Step title]
**Files**: `path/to/File.py`
**What**: Description of the change
**Pattern**: Reference to existing code that demonstrates the pattern to follow

### 2. [Step title]
...

## Testing Strategy
- What tests to write
- What existing tests might break

## Risks & Considerations
- Potential pitfalls
- Decisions that need clarification from the team

## Estimated Complexity
Low / Medium / High — with brief justification
```

### Rules
- Every step must reference concrete files and existing patterns
- Follow existing abstractions — do not invent new ones
- Identify dependencies between steps (what must happen first)
- Call out anything ambiguous that needs team input before starting
- Consider whether an ADR is needed for the approach

## Examples

- `/plan-issue 42` — Fetch issue #42 and create implementation plan
- `/plan-issue 123` — Plan implementation for issue #123

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Issue not found | Check the issue number: `gh issue list` |
| Issue is vague | List what needs clarification and suggest asking the issue author |
| Spans too many scopes | Break into sub-tasks and suggest splitting the issue |
| No existing pattern to follow | Flag this as a risk — may need an ADR for the new pattern |

---
name: implement-feedback-from-pr
description: >-
  Implement review feedback from a pull request. Fetches PR comments, distinguishes human from
  bot feedback, prioritizes and implements changes, then validates. Use when user says 'implement
  PR feedback', 'address review comments', 'fix PR review', 'apply PR suggestions', 'handle
  reviewer feedback', or 'implement changes from review'. Takes a PR number as argument.
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Implement PR Feedback - Turn Reviews into Improvements

Implement review feedback from a pull request. Use \$ARGUMENTS for the PR number.

## Process

1. Find your PR and fetch all review comments
2. Distinguish human feedback from bot suggestions
3. Prioritize and implement human feedback first
4. Critically evaluate automated feedback
5. Test your changes thoroughly

## Step 1: Fetch All Review Comments

```bash
gh pr view -c
```

## Step 2: Identify Feedback Sources

### Human Feedback (TOP PRIORITY)

Comments from team members, code reviewers, anyone with human names. These ask about design decisions, suggest better
approaches, point out logic issues, request clarification.

### Bot Feedback (EVALUATE CRITICALLY)

Common bots: SonarCloud (code quality/security), CodeQL (vulnerability scanning), test/linting/coverage bots. Bot
comments have systematic formatting and links to reports.

## Step 3: Implement Human Feedback First

For each human comment:

1. Navigate to the file mentioned
2. Make the requested change
3. Mark it as done

Handle common feedback types:

- "Can you explain why..." → Add code comment explaining reasoning
- "This could be simplified..." → Implement simplification, test
- "What happens if..." → Add error handling + test for edge case
- "Please add documentation..." → Update README or add docstrings

## Step 4: Evaluate Bot Feedback

- **SonarCloud Bugs/Vulnerabilities**: Almost always fix
- **Code Smells**: Usually worth fixing
- **Security Hotspots**: Evaluate case-by-case
- **Coverage drops**: Add tests only if they add value
- **Linting**: Run `make pr-ready` in affected scope

## Step 5: Validate Changes

```bash
cd affected_scope
poetry shell
make pr-ready
make test
exit
```

## Examples

**Typical invocation**: `/implement-feedback-from-pr 42`

**Common scenarios**:

1. Reviewer asks to simplify a function → refactor, test, commit
2. SonarCloud flags a code smell → evaluate and fix if valid
3. Reviewer requests documentation → add docstrings or update README
4. Coverage dropped → add targeted tests for new code paths

## Troubleshooting

| Problem                                    | Solution                                              |
| ------------------------------------------ | ----------------------------------------------------- |
| `gh pr view -c` shows no comments          | Check PR number is correct: `gh pr list`              |
| Cannot determine which files are affected  | Run `gh pr diff` to see all changed files             |
| Bot feedback conflicts with human feedback | Human feedback always takes priority                  |
| `make pr-ready` fails after changes        | Fix lint/type errors introduced by your fixes, re-run |

## Done When

- Every human comment addressed or responded to
- All critical bot warnings resolved
- Code passes all tests
- `make pr-ready` runs clean for all affected scopes

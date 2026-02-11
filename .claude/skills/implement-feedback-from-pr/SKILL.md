---
name: implement-feedback-from-pr
description: Implement review feedback from a pull request. Fetches PR comments,
  distinguishes human from bot feedback, prioritizes and implements changes,
  then validates.
disable-model-invocation: true
allowed-tools: Bash, Read, Edit, Grep, Glob
---

# Implement PR Feedback - Turn Reviews into Improvements

Implement review feedback from a pull request. Use $ARGUMENTS for the PR number.

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

Comments from team members, code reviewers, anyone with human names. These ask about design decisions, suggest better approaches, point out logic issues, request clarification.

### Bot Feedback (EVALUATE CRITICALLY)

Common bots: SonarCloud (code quality/security), CodeQL (vulnerability scanning), test/linting/coverage bots. Bot comments have systematic formatting and links to reports.

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

## Done When

- Every human comment addressed or responded to
- All critical bot warnings resolved
- Code passes all tests
- `make pr-ready` runs clean for all affected scopes

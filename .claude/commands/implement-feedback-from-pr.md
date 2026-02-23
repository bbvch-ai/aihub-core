# Implement PR Feedback - Turn Reviews into Improvements

Your PR has been reviewed! Time to turn that valuable feedback into code improvements. This cookbook guides you through
implementing review comments systematically and effectively.

## Overview

Here's your feedback implementation roadmap:

1. Find your PR and fetch all review comments
2. Distinguish human feedback from bot suggestions
3. Prioritize and implement human feedback first
4. Critically evaluate automated feedback
5. Test your changes thoroughly

## Your Feedback Implementation Cookbook

### Step 1: Fetch All Review Comments

Time to gather all the feedback in one place:

```bash
# Get all comments on your PR (replace 123 with your PR number)
gh pr view -c
```

### Step 2: Identify the Feedback Sources

Not all feedback is created equal! Here's how to categorize it:

#### Human Feedback (TOP PRIORITY)

Look for comments from:

- Team members (check the username)
- Code reviewers assigned to your PR
- Anyone with actual human names

These comments often:

- Ask questions about design decisions
- Suggest better approaches
- Point out business logic issues
- Request clarification or documentation

#### Bot Feedback (EVALUATE CRITICALLY)

Common bots include:

- **SonarCloud**: Code quality and security issues
- **CodeQL**: Security vulnerability scanning
- **Test bots**: Failing test reports
- **Linting bots**: Style violations
- **Coverage bots**: Test coverage reports

Bot comments usually:

- Have systematic formatting
- Include links to detailed reports
- Use technical jargon
- Come from users with "bot" or "app" in their name

### Step 3: Implement Human Feedback First

Human feedback is gold - implement it thoroughly:

```bash
# For each human comment:
# 1. Navigate to the file mentioned
# 2. Make the requested change
# 3. Mark it as done in your checklist
```

#### Common types of human feedback and how to handle them:

**"Can you explain why..."**

- Add a comment in the code explaining your reasoning
- Consider if the code could be more self-explanatory

**"This could be simplified..."**

- Implement the suggested simplification
- Test to ensure functionality remains intact

**"What happens if..."**

- Add error handling for the edge case
- Write a test to cover this scenario

**"Please add documentation..."**

- Update the relevant README or add docstrings
- Include usage examples if requested

### Step 4: Critically Evaluate Bot Feedback

Bots aren't always right! Here's how to assess their suggestions:

#### SonarCloud Issues

```bash
# Check the specific issue type:
# - Code Smells: Usually worth fixing
# - Bugs: Almost always fix these
# - Vulnerabilities: MUST fix
# - Security Hotspots: Evaluate case-by-case
```

Questions to ask:

- Is this a real issue or a false positive?
- Does fixing it improve the code?
- Is the bot misunderstanding the context?

#### Test Coverage Warnings

```bash
# If coverage dropped:
# 1. Check which lines aren't covered
# 2. Decide if they need tests
# 3. Add tests only if they add value
```

Remember: 100% coverage isn't always the goal!

#### Linting Issues

```bash
# These are usually straightforward:
cd affected_scope
make pr-ready
# This should fix most linting issues automatically
```

### Step 5: Make Your Changes

Now implement the feedback systematically:

### Step 6: Validate Your Changes

After implementing feedback, ensure everything still works:

```bash
# Run the full validation suite
# (You know this from create-pr.md!)

# Format and lint each affected scope
cd affected_scope
make pr-ready

# Run tests for each affected scope
cd affected_scope
make test

# Check that you haven't broken anything new
git diff
```

## You're Done When...

- Every human comment has been addressed or responded to
- All critical bot warnings are resolved
- Your code still passes all tests
- Make pr-ready runs clean for all affected scopes
- You have clear responses prepared for any feedback you didn't implement
- You understand why you made each change

Remember: Good code review feedback makes your code better. Embrace it!

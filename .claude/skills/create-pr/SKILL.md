---
name: create-pr
description: Pre-pull request validation and preparation. Run formatting, linting,
  type checking, and tests across all affected scopes before creating a PR.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob, Edit
---

# Create PR - Pre-Pull Request Validation Command

You're about to prepare your code for a pull request. Follow this comprehensive validation cookbook to ensure your
changes meet all quality standards and pass all checks.

## Overview

Here's what you need to do:

1. Commit your current work using semantic commits
2. Format and lint all code across every scope
3. Run all tests and fix any failures
4. Review your changes against the main branch
5. Validate adherence to our coding standards
6. Fix any issues you find along the way
7. Update documentation if needed

## Your Step-by-Step Cookbook

### Step 1: Commit Your Current State

Before diving into validation, let's save your current work. Use semantic commits following our convention:

```bash
# First, see what you've changed
git status
git diff

# Stage your changes (be selective!)
git add <files>

# Commit with a semantic message
# Format: <type>(<scope>): <subject>
# Types: fix, feat, test, doc, chore
# Example: feat(agent): Add retry logic to RAG agent
git commit -m "type(scope): Your descriptive message"
```

Remember:

- Keep commits focused - one logical change per commit
- Write clear, imperative messages ("Add feature" not "Added feature")
- If you have multiple unrelated changes, create multiple commits

### Step 2: Format and Lint Your Code

Time to make your code squeaky clean! Navigate to each scope and run the quality checks. When you encounter errors, fix
them immediately and re-run until everything passes:

```bash
# Start with the core library - this is the foundation everything depends on
cd aihub_lib
poetry shell
make pr-ready
# Got errors? Fix them now and run make pr-ready again until it's green!
exit

# Next, tackle the pipeline scope
cd ../aihub_pipeline
poetry shell
make pr-ready
exit

# Move on to the agent scope
cd ../aihub_agent
poetry shell
make pr-ready
exit

# Process scope is next
cd ../aihub_process
poetry shell
make pr-ready
exit

# Almost there! Check the API scope
cd ../aihub_api
poetry shell
make pr-ready
exit

# Finally, the bot scope
cd ../aihub_bot
poetry shell
make pr-ready
exit

# Great! Return to the project root
cd ..
```

### Step 3: Make All Tests Pass

Now it's time to ensure your code actually works! Run the test suite for each scope:

1. Read the error message carefully - understand what's breaking
2. Fix the root cause (never disable or skip tests!)
3. Re-run the tests until you see green

```bash
cd aihub_lib && poetry shell && make test && exit
cd ../aihub_pipeline && poetry shell && make test && exit
cd ../aihub_agent && poetry shell && make test && exit
cd ../aihub_process && poetry shell && make test && exit
cd ../aihub_api && poetry shell && make test && exit
cd ../aihub_bot && poetry shell && make test && exit
cd ..
```

### Step 4: Review Your Changes

Look at every single change you've made:

```bash
git diff main...HEAD
```

Inspection checklist:

1. **Hunt for bugs**: edge cases, null pointers, resource leaks, race conditions
2. **Enforce coding standards**: comments explain "why", docstrings on public APIs, type annotations everywhere, Pydantic models over dicts, fail fast error handling, snake_case naming
3. **Respect the architecture**: code in the right scope, shared code in aihub_lib, no customer-specific information

### Step 5: Fix What You Found

1. Fix each problem properly
2. Re-run `make pr-ready` and `make test` for affected scopes
3. Verify fixes actually solved the problems

### Step 6: The Final Check

1. Run `git status` - inventory everything you've touched
2. Run `git diff` one more time - final read-through
3. Ask: "Does this solve exactly what the task asked for?"

### Step 7: Update Documentation

Follow the /update-doc skill instructions to ensure documentation stays in sync with code changes.

## Critical Rules

- **COMMIT** strategically - use semantic commits for logical changes
- **STOP!** Do NOT create a pull request - you're just preparing
- **STOP!** Do NOT skip any failing test - every single one must pass
- **FIX** the actual problem, not the symptom
- **FOLLOW** typing and documentation standards
- **UPDATE** documentation when changes affect it

## You're Done When

- Changes are committed with proper semantic commit messages
- Every `make pr-ready` runs clean
- Every `make test` shows all green
- Git diff is spotless
- Code does exactly what was asked
- Documentation is updated

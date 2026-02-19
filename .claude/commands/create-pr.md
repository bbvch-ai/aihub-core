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
make pr-ready
# Got errors? Fix them now and run make pr-ready again until it's green!

# Next, tackle the pipeline scope
cd ../aihub_pipeline
make pr-ready
# Keep fixing and re-running until all checks pass

# Move on to the agent scope
cd ../aihub_agent
make pr-ready
# Don't proceed until this is completely clean

# Process scope is next
cd ../aihub_process
make pr-ready
# Fix any issues before moving forward

# Almost there! Check the API scope
cd ../aihub_api
make pr-ready
# Resolve all formatting and linting issues

# Finally, the bot scope
cd ../aihub_bot
make pr-ready
# One last set of fixes if needed

# Great! Return to the project root
cd ..
```

### Step 3: Make All Tests Pass

Now it's time to ensure your code actually works! Run the test suite for each scope. Here's your game plan when tests
fail:

1. Read the error message carefully - understand what's breaking
2. Fix the root cause (never disable or skip tests!)
3. Re-run the tests until you see that satisfying green checkmark

```bash
# Test the core library first - everything depends on this!
cd aihub_lib
make test
# Red test? Stop here, fix it, and run make test again

# Pipeline tests - ensure your data processing works
cd ../aihub_pipeline
make test
# Don't move on until every test is green

# Agent tests - verify your AI agents behave correctly
cd ../aihub_agent
make test
# Failed test = broken agent. Fix it now!

# Process tests - check your business workflows
cd ../aihub_process
make test
# A failing process test means broken automation

# API tests - ensure your endpoints work properly
cd ../aihub_api
make test
# Your API must be rock solid before proceeding

# Bot tests - verify chat functionality
cd ../aihub_bot
make test
# Users depend on this - make it perfect

# Excellent! Back to home base
cd ..
```

### Step 4: Review Your Changes Like a Hawk

Time to put on your reviewer hat! Look at every single change you've made:

```bash
git diff main...HEAD
```

Here's your inspection checklist:

1. **Hunt for bugs before they hunt you**

   - Did you handle all edge cases?
   - Could anything throw a null pointer exception?
   - Are you leaking any resources?
   - Any race conditions lurking in concurrent code?

2. **Enforce our coding standards religiously**

   - **Comments**: Do they explain "why" not "what"? Bad: `# Increment counter`. Good:
     `# Retry 3 times to handle transient network errors`
   - **Docstrings**: Every public module, class, method, and function needs one. No exceptions!
   - **Type annotations**: Every variable, argument, and return value must have types. We're strict about this!
   - **Complex types**: See a raw dict or tuple? Stop! Create a Pydantic model or dataclass instead
   - **Error handling**: Let functions fail fast and loud. Never swallow exceptions with a silent None return
   - **Naming conventions**: Everything must be snake_case. No camelCase, no PascalCase for files/directories

3. **Respect the architecture**

   - Is your code in the right scope? Shared code belongs in aihub_lib
   - Zero customer-specific information in the core repository
   - Each component should stay in its lane

### Step 5: Fix What You Found

Found issues? Here's your fix-it protocol:

1. Jump into the files and fix each problem properly
2. After each fix, go back and re-run `make pr-ready` and `make test` for that scope
3. Double-check that your fixes actually solved the problems (don't assume!)

### Step 6: The Final Check

You're almost there! Let's do one last sweep:

1. Run `git status` - take inventory of everything you've touched
2. Run `git diff` one more time - give it a final read-through with fresh eyes
3. Ask yourself: "Does this solve exactly what the task asked for?"

### Step 7: Update Documentation

Before you wrap up, documentation needs love too! Follow the instructions in our documentation update guide:

```bash
# Check out the documentation update command
cat .claude/commands/update-doc.md
```

Follow those instructions carefully - they'll guide you through:

- Checking if your changes require documentation updates
- Updating relevant README files
- Ensuring documentation stays in sync with the code

This step is CRUCIAL - good code without good docs is only half the job!

## Critical Rules to Remember

- **COMMIT** strategically - use semantic commits for logical changes
- **STOP!** Do NOT create a pull request - you're just preparing
- **STOP!** Do NOT skip any failing test - every single one must pass
- **FIX** the actual problem, not the symptom - no band-aids allowed
- **FOLLOW** our typing and documentation standards - they're non-negotiable
- **UPDATE** documentation when your changes affect it

## You're Done When...

✅ Your changes are committed with proper semantic commit messages\
✅ Every `make pr-ready` runs clean (no errors, no warnings)\
✅ Every `make test` shows all green (zero failures)\
✅ Your git diff is spotless (no bugs, perfect standards)\
✅ Your code does exactly what was asked - nothing more, nothing less\
✅ Documentation is updated to reflect your changes

Now you're ready for someone else to create that PR! 🎉

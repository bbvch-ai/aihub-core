# Update Documentation - Keep Your Docs in Sync Command

Great code without great docs is only half the job! This cookbook guides you through updating documentation to match
your code changes. Remember: documentation is not an afterthought - it's an integral part of every change you make.

## Overview

Here's your documentation checklist:

1. Review what you've changed in your code
2. Read all potentially affected README files
3. Identify documentation that needs updates
4. Fix inaccurate documentation
5. Add missing documentation
6. Create new README files where needed

## Your Documentation Cookbook

### Step 1: Survey Your Changes

First, understand the full scope of what you've modified:

```bash
# See all your changes compared to main
git diff main...HEAD

# Get a high-level view of changed files
git diff --name-only main...HEAD
```

Take mental notes:

- Which scopes did you touch?
- Did you add new features or change existing behavior?
- Did you discover any undocumented quirks or requirements?

### Step 2: Read the Documentation Landscape

Time to become a documentation detective! Read every README that could be affected by your changes:

```bash
# Start at the root - this is your foundation
cat README.md

# Now check each scope you modified
# If you changed aihub_agent:
cat aihub_agent/README.md

# If you changed aihub_api:
cat aihub_api/README.md

# Continue for each affected scope...
```

Pro tip: Also check for README files in subdirectories of the scopes you modified:

```bash
# Find all README files in a scope
find aihub_agent -name "README.md" -type f

# Or use fd if you have it installed
fd README.md aihub_agent
```

### Step 3: The Critical Questions

As you read each README, ask yourself these mandatory questions:

#### 🔍 Is the documentation now wrong?

Your code changes might have made existing documentation incorrect. Common culprits:

- Changed function signatures or behavior
- Modified workflow steps
- Updated configuration requirements
- Altered architectural patterns

#### 🤔 What's missing that would have helped you?

Think back to when you started your task:

- What did you have to figure out on your own?
- What gotchas did you encounter?
- What context would have saved you time?
- What dependencies or setup steps weren't documented?

#### ⚔️ Does the documentation conflict with reality?

Remember: **Code is ALWAYS the ground truth!**

- If the README says one thing but the code does another, fix the README
- Remove outdated information ruthlessly
- Update examples that no longer work

### Step 4: Fix Inaccurate Documentation

Found something wrong? Fix it immediately:

```bash
# Navigate to the file location
cd aihub_agent

# Edit the README
# Update the incorrect sections to match your code changes
# Be specific and clear about the new behavior
```

Examples of what to update:

- API endpoints that changed
- Configuration parameters that were added/removed
- Workflow steps that now work differently
- Dependencies that are now required

### Step 5: Add Missing Documentation

Identified gaps? Fill them in! Here's what to document:

#### For new features:

- What does it do?
- How do you use it?
- What are the configuration options?
- Any limitations or considerations?

#### For discovered knowledge:

- Setup steps you had to figure out
- Tricky integration points
- Performance considerations
- Common pitfalls and how to avoid them

### Step 6: Create New README Files

Sometimes you need a fresh README at a more specific level:

```bash
# If you added a new major component to aihub_agent/new_component/
cd aihub_agent/new_component
touch README.md
```

What warrants a new README?

- New subdirectories with multiple files
- Complex features that need dedicated explanation
- Standalone components within a scope

#### 📝 Writing Style for READMEs

- **Be VERY concise but complete**: Every word should add value
- **Write for your future self**: Assume you'll forget everything
- **Include "why" not just "what"**: Context matters

#### 🎯 Scope Rules for Documentation

- **Root README**: Platform-wide information only
- **Scope-level README**: Broad overview of the entire package
- **Subdirectory README**: Specific to that component
- **Deep folder README**: Very specific functionality

#### DOs and DONTs

- **DO** keep it as brief as possible. Documentation is hard to maintain, so we should keep it useful but minimal

- **DO** assume developers can just write the code themselves if they want to go into more details

- **DO** aggregate information from multiple files within a README

- **DO** Talk on a high-level: What are we trying to achieve here, why do we need that, what's the general philosophy
  and idea

- **DO NOT** Copy over code, as this is guaranteed to fall out of sync very quickly

- **DO NOT** include ANY markdown code blocks that show how this code can be imported or used. That is an indication
  that your documentation is too low-level

- **DO NOT** Talk on a low level about specific code files

- **DO NOT** simply state what is going on in the code - add higher level info and context

- **DO NOT** state the obvious or repeat what the docstring say

- **DO NOT** create a README just for one file. Documentation should live within the docstrings of the code itself!

### Documentation Standards

Follow these rules religiously:

#### 📝 Writing Style

- Be concise but complete
- Use examples liberally
- Write for your future self who forgot everything
- Include "why" not just "what"

#### 🎯 Scope Rules

- **Scope-level README**: Broad overview of the entire package
- **Subdirectory README**: Specific to that component
- **Root README**: Platform-wide information only

### The Golden Rules

1. **Documentation evolves with code** - They're inseparable twins
2. **Code is truth** - When in doubt, the code wins
3. **Future you will thank current you** - Document what you wish you had known
4. **No documentation debt** - Fix it now, not "later"
5. **Respect scope** - Edit the smallest possible README.md, only edit the root level README.md if your change is large
   enough to justify it

## You're Done When...

✅ Every README affected by your changes is updated\
✅ All inaccurate documentation is corrected\
✅ Missing information that would have helped you is added\
✅ New components have appropriate README files\
✅ Someone new could understand your changes from the docs alone

Remember: Well-documented code is a gift to your future self and your teammates! 📚

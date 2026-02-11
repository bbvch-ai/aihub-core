---
name: update-doc
description: Synchronize documentation with code changes. Reviews affected READMEs,
  identifies stale documentation, and updates or creates missing docs.
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Update Documentation - Keep Your Docs in Sync

Guide for updating documentation to match code changes.

## Overview

1. Review what you've changed in your code
2. Read all potentially affected README files
3. Identify documentation that needs updates
4. Fix inaccurate documentation
5. Add missing documentation
6. Create new README files where needed

## Step 1: Survey Your Changes

```bash
git diff main...HEAD
git diff --name-only main...HEAD
```

Note: Which scopes did you touch? New features or changed behavior? Undocumented quirks?

## Step 2: Read the Documentation Landscape

Read every README that could be affected by changes:

- Start with the project root README
- Check each scope-level README
- Find all README files in subdirectories of modified scopes

## Step 3: The Critical Questions

As you read each README, ask:

- **Is documentation now wrong?** Changed signatures, workflows, config, patterns?
- **What's missing that would have helped you?** Gotchas, dependencies, setup steps?
- **Does documentation conflict with reality?** Code is ALWAYS ground truth — fix the README.

## Step 4: Fix Inaccurate Documentation

Update incorrect sections to match code changes. Examples: API endpoints, config parameters, workflow steps, dependencies.

## Step 5: Add Missing Documentation

For new features: what it does, how to use it, config options, limitations.
For discovered knowledge: setup steps, integration points, performance considerations, pitfalls.

## Step 6: Create New README Files

Create when: new subdirectories with multiple files, complex features, standalone components.

Do NOT create when: folder has very few files, code is easy to read, docstrings are sufficient.

### Writing Style

- **Be VERY concise but complete**: Every word should add value
- **Write for your future self**: Assume you'll forget everything
- **Include "why" not just "what"**: Context matters
- **DO NOT** copy over code (falls out of sync quickly)
- **DO NOT** include import/usage code blocks (too low-level)
- **DO NOT** create a README just for one file

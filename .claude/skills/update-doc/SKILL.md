---
name: update-doc
description: "Synchronize documentation with code changes by reviewing affected READMEs,
  identifying stale docs, and updating or creating missing documentation. Use when
  user says 'update docs', 'sync documentation', 'fix README', 'docs are outdated',
  'update the README', or after any code change that affects documented behavior.
  Covers root README, scope READMEs, and subdirectory docs."
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Update Documentation - Sync Docs with Code Changes

Ensure all documentation accurately reflects current code. Finds stale READMEs, updates incorrect information, adds
missing docs, and creates new READMEs where needed.

## Steps

### 1. Survey Your Changes

```bash
git diff main...HEAD
git diff --name-only main...HEAD
```

Determine: Which scopes were touched? New features or changed behavior? Undocumented quirks?

### 2. Read the Documentation Landscape

Read every README that could be affected:

- `/home/user/aihub-core/README.md` (project root)
- Scope-level READMEs (e.g., `aihub_api/README.md`)
- Subdirectory READMEs within modified scopes

### 3. Evaluate Each README Against Code

For each README, ask:

- **Is it now wrong?** Changed signatures, workflows, config, patterns?
- **What is missing?** Gotchas, dependencies, setup steps that would have helped?
- **Does it conflict with reality?** Code is ALWAYS ground truth -- fix the README.

### 4. Fix Inaccurate Documentation

Update incorrect sections to match code. Common targets:
- API endpoints and parameters
- Configuration options and defaults
- Workflow steps and prerequisites
- Dependency lists and version requirements

### 5. Add Missing Documentation

- **New features**: what it does, how to use it, config options, limitations
- **Discovered knowledge**: setup steps, integration points, pitfalls

### 6. Create New README Files (If Needed)

**Create when**: new subdirectories with multiple files, complex features, standalone components.

**Do NOT create when**: folder has very few files, code is self-explanatory, docstrings are sufficient.

## Writing Style

- Be VERY concise but complete -- every word should add value
- Write for your future self -- assume you will forget everything
- Include "why" not just "what" -- context matters
- DO NOT copy over code (falls out of sync quickly)
- DO NOT include import/usage code blocks (too low-level)
- DO NOT create a README just for one file

## Examples

**Typical invocation**: `/update-doc` after completing a feature or refactor

**Scope of changes**: If you modified `aihub_api/aihub_api/controller/agent.py`, check:
- `aihub_api/README.md` for API endpoint docs
- Root `README.md` for any high-level changes
- Subdirectory READMEs near the modified file

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Unsure which READMEs to update | Run `git diff --name-only main...HEAD` and check for READMEs in those directories |
| README references removed code | Delete or rewrite the section -- do not leave stale references |
| No README exists for new complex directory | Create one following the writing style above |
| Conflicting information across READMEs | Code is ground truth -- update all READMEs to match |

## Done When

- All READMEs in affected scopes are accurate
- No stale references to old code, endpoints, or config
- New features have appropriate documentation
- Writing style guidelines are followed

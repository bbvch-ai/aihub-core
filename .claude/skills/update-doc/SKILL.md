---
name: update-doc
description: Synchronize documentation with code changes by reviewing affected READMEs, CLAUDE.md files, and skills. Use when user says 'update docs', 'sync documentation', 'fix README', 'docs are outdated', 'update the README', 'sync skills with code', or after any code change that affects documented behavior. Covers root README, scope READMEs, CLAUDE.md files, skills, and subdirectory docs.
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# Update Documentation - Sync Docs, CLAUDE.md, and Skills with Code Changes

Ensure all documentation, CLAUDE.md files, and skills accurately reflect current code. Finds stale content, updates
incorrect information, and adds missing documentation.

## Steps

### 1. Survey Your Changes

```bash
git diff main...HEAD
git diff --name-only main...HEAD
```

Determine: Which scopes were touched? New features or changed behavior? Changed patterns or conventions?

### 2. Update READMEs

Read every README that could be affected:

- `/home/user/aihub-core/README.md` (project root)
- Scope-level READMEs (e.g., `aihub_api/README.md`)
- Subdirectory READMEs within modified scopes

For each README, ask:

- **Is it now wrong?** Changed signatures, workflows, config, patterns?
- **What is missing?** Gotchas, dependencies, setup steps that would have helped?
- **Does it conflict with reality?** Code is ALWAYS ground truth -- fix the README.

### 3. Update CLAUDE.md Files

Check if changes affect AI assistant context:

- **Root `CLAUDE.md`**: Changed conventions, new tools, new commands, new access points
- **Scope `CLAUDE.md`**: Changed architecture, new patterns, renamed files, new directories
- **File paths**: If files were moved or renamed, update all path references in CLAUDE.md files

### 4. Update Skills

Check if changes affect any skills in `.claude/skills/`:

- **Scaffold skills**: If the pattern for creating new components changed, update the scaffold template
- **Debug skills**: If error messages, file locations, or diagnostic steps changed, update them
- **Reference skills**: If API patterns, event structures, or configuration changed, update references
- **File paths in skills**: If referenced files were moved or renamed, update the skill

Search for affected skills:

```bash
# Find skills that reference modified files
git diff --name-only main...HEAD | while read f; do
  grep -rl "$(basename $f)" .claude/skills/ 2>/dev/null
done | sort -u
```

### 5. Fix Inaccurate Documentation

Update incorrect sections to match code. Common targets:

- API endpoints and parameters
- Configuration options and defaults
- Workflow steps and prerequisites
- File paths and directory structures
- Code patterns and examples in skills

### 6. Add Missing Documentation

- **New features**: what it does, how to use it, config options, limitations
- **Discovered knowledge**: setup steps, integration points, pitfalls

### 7. Create New README Files (If Needed)

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
- `aihub_api/CLAUDE.md` for AI assistant context
- Root `README.md` for any high-level changes
- `.claude/skills/scaffold-api-endpoint/SKILL.md` if the controller pattern changed

## Troubleshooting

| Problem                                    | Solution                                                                       |
| ------------------------------------------ | ------------------------------------------------------------------------------ |
| Unsure which docs to update                | Run `git diff --name-only main...HEAD` and check for docs in those directories |
| README references removed code             | Delete or rewrite the section -- do not leave stale references                 |
| Skill references moved file                | Update the file path in the skill                                              |
| CLAUDE.md has stale architecture           | Rewrite the section to match current code structure                            |
| No README exists for new complex directory | Create one following the writing style above                                   |

## Done When

- All READMEs in affected scopes are accurate
- CLAUDE.md files reflect current architecture and patterns
- Skills reference correct file paths and patterns
- No stale references to old code, endpoints, or config
- New features have appropriate documentation

---
name: update-doc
description: Synchronize documentation with code changes across the aihub-core monorepo. Reviews READMEs, CLAUDE.md files, skills, agents, and VitePress docs for staleness. Use when user says 'update docs', 'sync documentation', 'fix README', 'docs are outdated', 'update the README', 'sync skills with code', or after any code change that affects documented behavior. Do NOT use for writing new feature docs from scratch (use /document-feature) or creating ADRs (use /document-decision).
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# Update Documentation - Sync Docs with Code Changes

Sync all documentation across the aihub-core monorepo after code changes. Code is always ground truth — when docs and
code disagree, fix the docs.

For thorough, multi-scope documentation reviews (e.g., before a large PR), consider launching the `doc-sync` subagent
instead — it runs in its own context window and produces a structured report.

## Step 1: Survey Changes

```bash
git diff --name-only main...HEAD
git diff --stat main...HEAD
```

Identify which scopes were touched and whether public APIs, patterns, or architecture changed.

## Step 2: Identify Documentation Targets

Documentation lives in 5 locations. Check each for staleness against your changes:

### 2a. README.md Files

- `README.md` — project root (setup, architecture overview)
- `{scope}/README.md` — scope-level (e.g., `aihub_api/README.md`, `aihub_agent/README.md`)
- Subdirectory READMEs within modified scopes (e.g., `aihub_lib/aihub_lib/auth/README.md`)

### 2b. CLAUDE.md Files

- `CLAUDE.md` — root (conventions, tooling, commands, access points, quick reference tables)
- `{scope}/CLAUDE.md` — scope-level (folder structure, patterns, key classes, essential files)

### 2c. Skills (`.claude/skills/*/SKILL.md`)

```bash
# Find skills that reference any modified file
git diff --name-only main...HEAD | while read f; do
  grep -rl "$(basename "$f")" .claude/skills/ 2>/dev/null
done | sort -u
```

Check scaffold skills if component patterns changed, debug skills if error paths changed, reference skills if APIs or
events changed.

### 2d. Agents (`.claude/agents/*.md`)

```bash
# Find agents that reference modified paths
git diff --name-only main...HEAD | while read f; do
  grep -rl "$(basename "$f")" .claude/agents/ 2>/dev/null
done | sort -u
```

### 2e. VitePress Docs (`aihub_doc/docs/**/index.en.md`)

- `aihub_doc/docs/2_platform/` — platform architecture, services, deployment
- `aihub_doc/docs/3_sdk/` — SDK patterns, agent/pipeline/process building
- `aihub_doc/docs/4_ecosystem/` — contributing guidelines, AI tooling
- `aihub_doc/docs/5_references/` — API references, troubleshooting

**VitePress rules**:

- Only edit `index.en.md` — never edit `index.de.md` (auto-translated)
- `docs/6_code_deep_dive/` is auto-synced from README files via `sync-docs.sh` — update the source README, not the
  synced copy

## Step 3: Review and Fix

For each documentation target, read the doc file and the code it describes. Ask:

- **Wrong?** Outdated paths, renamed classes, changed APIs, removed features, wrong config
- **Missing?** New features undocumented, new patterns not captured, new files not listed
- **Redundant?** Describes deleted code, references removed files, covers obsolete patterns

Fix what you find. Preserve each file's existing style and level of detail. Don't inline code — reference file paths
instead.

## Step 4: Verify No Stale Paths Remain

```bash
# Spot-check that paths referenced in changed docs still exist
grep -ohE '["`][a-zA-Z_./]+/[a-zA-Z_.]+["`]' {changed-doc-files} | tr -d '"`' | while read p; do
  [ ! -e "$p" ] && echo "STALE: $p"
done
```

## Example

If you modified `aihub_api/aihub_api/routes/agent/AgentController.py`, check:

- `aihub_api/README.md` — API endpoint docs
- `aihub_api/CLAUDE.md` — route patterns, key classes
- `.claude/skills/scaffold-api-endpoint/SKILL.md` — controller pattern template
- `.claude/agents/architect.md` — if it references the agent route structure

## Done When

- All READMEs in affected scopes match current code
- CLAUDE.md files reflect current architecture, paths, and patterns
- Skills and agents reference correct file paths and patterns
- VitePress docs updated (only `index.en.md`, never `index.de.md`)
- No stale path references remain

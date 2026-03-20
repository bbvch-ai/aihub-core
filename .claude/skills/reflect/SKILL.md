---
name: reflect
description: Reflect on the current coding session to identify where Claude violated swiss-ai-hub conventions, missed patterns, or needed steering. Proposes targeted improvements to CLAUDE.md files, skills, agents, or hooks. Use when user says 'reflect on this session', 'what went wrong', 'improve the prompts', 'update CLAUDE.md based on this session', 'session retrospective', 'what should we improve', or 'learn from mistakes'. Do NOT use for full CLAUDE.md audit (use /create-or-audit-claude-md), skill review (use /create-or-audit-skill), or documentation sync (use /update-doc).
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Reflect - Session Retrospective & Prompt Improvement

Analyze the current session to identify where Claude violated this codebase's conventions or needed user steering.
Propose concrete improvements to prevent recurrence.

## Step 1: Analyze the Session Against Known Conventions

Review the conversation history. Check specifically for violations of these root CLAUDE.md coding conventions:

- **#1 Type hints**: Missing return types, missing `Annotated`, using `Optional[str]` instead of `str | None`
- **#2 Pydantic over dicts**: Used dicts or dataclasses where Pydantic models are required
- **#3 Fail fast**: Added defensive try-catch, caught errors to return None
- **#4 No comments**: Added comments explaining what code does (not why)
- **#10 Modern Python**: Used `TypeVar` instead of PEP 695 generics, `"ClassName"` instead of `Self`
- **#13 One class per file**: Put multiple classes in one file
- **#14 No loose functions**: Created standalone functions instead of service class methods
- **#15 No backwards compat**: Added compatibility shims, re-exports, or renamed aliases
- **#16 No new abstractions**: Introduced patterns not already in the codebase

Also look for:

- **Architecture mistakes**: Misunderstood Controller → Service → Entity layers, NATS pub/sub, event hierarchy
- **Scope boundary violations**: Imported directly between scopes instead of through `packages/core`
- **Stale knowledge**: Used Poetry commands (migrated to uv), referenced non-existent paths
- **Steering moments**: Places where the user said "no", "don't do that", "instead do X"
- **Repeated corrections**: The same issue flagged multiple times

## Step 2: Categorize and Target Improvements

For each issue, determine the right fix:

| Category         | When to Use                                        | Target                                               |
| ---------------- | -------------------------------------------------- | ---------------------------------------------------- |
| **Convention**   | Claude violated a coding convention                | Root `CLAUDE.md` (conventions 01-16)                 |
| **Architecture** | Claude misunderstood how scopes/components connect | Scope CLAUDE.md (one of the 10 scope files)          |
| **Skill fix**    | A skill gave wrong instructions or missed a step   | `.claude/skills/*/SKILL.md` (validate after editing) |
| **New skill**    | A multi-step workflow keeps recurring              | New `.claude/skills/` directory                      |
| **Agent fix**    | A subagent lacked necessary context                | `.claude/agents/*.md`                                |
| **Hook**         | A deterministic rule should be auto-enforced       | `.claude/settings.json` hooks section                |

Scope CLAUDE.md files that can be improved:

- `packages/core/CLAUDE.md` — shared patterns, events, entities, NATS, auth
- `packages/api/CLAUDE.md` — route patterns, FastAPI conventions, DTOs
- `packages/agent/CLAUDE.md` — agent workflow, config/form duality, LlamaIndex
- `packages/pipeline/CLAUDE.md` — Dagster assets, resources, IO managers
- `packages/process/CLAUDE.md` — process orchestration, work events, forms
- `packages/bot/CLAUDE.md` — handler architecture, CompletionHandler pattern
- `packages/web/CLAUDE.md` — Nuxt/Vue/PrimeVue conventions, composables
- `docs/CLAUDE.md` — VitePress docs, translation rules
- `infra/deployment/CLAUDE.md` — Docker Compose, Traefik, network zones

**Prefer hooks over CLAUDE.md** when the rule is deterministic (always do X after Y). Existing hooks handle formatting,
linting, scope boundary checks, and sensitive file protection — check `.claude/settings.json` before adding a CLAUDE.md
rule that a hook could enforce.

## Step 3: Propose Changes

For each improvement, provide:

1. **Issue**: What went wrong
2. **Evidence**: The specific conversation moment (quote the user's correction)
3. **Root cause**: Why current docs/skills didn't prevent this
4. **Fix**: Exact file, section, and content to add or change
5. **Prevention**: How this stops it from happening again

Only propose changes for issues that would affect multiple future sessions — one-off mistakes don't warrant doc changes.

## Step 4: Apply Changes (with user approval)

Present all proposals, then ask which to apply. When editing:

- For skill changes, run validation after: `bash .claude/skills/create-or-audit-skill/scripts/validate-skill.sh`
- For CLAUDE.md changes, read the existing section first to avoid contradictions
- Keep changes minimal — one focused addition per issue, not a rewrite

## Common Patterns in This Codebase

Issues that have come up before:

- Using `poetry` commands instead of `uv` (project migrated to uv in Feb 2026)
- Using `gh` CLI instead of GitHub MCP tools (`mcp__github__issue_read`, `mcp__github__pull_request_read`)
- Creating `controller/` directories instead of `routes/` in packages/api
- Missing the double-nesting convention: `{scope}/{scope}/` for source code
- Not reading scope CLAUDE.md before working in a scope
- Adding backwards-compatible aliases when refactoring

## Troubleshooting

| Problem                                 | Solution                                                          |
| --------------------------------------- | ----------------------------------------------------------------- |
| Session was mostly Q&A, no code         | Focus on knowledge gaps rather than coding patterns               |
| Too many issues to fix at once          | Prioritize by frequency — fix the most recurring issue first      |
| Proposed change conflicts with existing | Resolve the conflict — update or remove the old rule              |
| Unclear if issue is one-off or systemic | Only add to CLAUDE.md if it would affect multiple future sessions |
| Issue is better handled by a hook       | Propose a hook in `.claude/settings.json` instead                 |

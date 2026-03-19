---
name: plan-issue
description: Fetch a GitHub issue from bbvch-ai/aihub-core and create an implementation plan using monorepo scope analysis, ADR checks, and scaffold skill mapping. Use when user says 'plan this issue', 'how should I implement issue #X', 'plan implementation', 'break down this issue', 'fetch issue and plan', 'what needs to change for #X', or 'implementation strategy for issue'. Takes an issue number as argument. Do NOT use for directly implementing code (use plan mode), PR feedback (use /implement-feedback-from-pr), or code review (use /review-diff).
allowed-tools: Bash, Read, Grep, Glob
---

# Plan Issue - GitHub Issue to Implementation Plan

Fetch issue \$ARGUMENTS from `bbvch-ai/aihub-core` and produce a scoped implementation plan.

## Step 1: Fetch the Issue

Use the GitHub MCP server to gather structured issue data:

1. **Issue details**: `mcp__github__issue_read` with `method: "get"` — title, body, author, assignees, milestone
2. **Discussion**: `mcp__github__issue_read` with `method: "get_comments"` — clarifications, decisions, context
3. **Sub-issues**: `mcp__github__issue_read` with `method: "get_sub_issues"` — task breakdown if present
4. **Labels**: `mcp__github__issue_read` with `method: "get_labels"` — categorization and priority

All calls use `owner: "bbvch-ai"`, `repo: "swiss-ai-hub"`, `issue_number: $ISSUE_NUMBER`.

Optionally check the project board for priority and status context:

```bash
gh project item-list 13 --owner bbvch-ai --format json | jq '.items[] | select(.content.number == $ISSUE_NUMBER)'
```

Extract from the issue: **Goal** (what needs to be achieved), **Constraints** (requirements or limitations), **Context**
(related issues, PRs, or decisions).

## Step 2: Identify Affected Scopes

Map the issue requirements to monorepo scopes:

| Scope               | Responsibility                                                 |
| ------------------- | -------------------------------------------------------------- |
| `packages/core`     | Shared library (events, entities, NATS, auth, config)          |
| `packages/api`      | REST API + WebSocket gateway (FastAPI controllers, services)   |
| `packages/agent`    | AI agent definitions and workflows (LlamaIndex)                |
| `packages/pipeline` | Data ingestion pipelines (Dagster assets, resources)           |
| `packages/process`  | Business process orchestration (agent + human + program steps) |
| `packages/bot`      | Collaboration platform integrations (MS Teams, Slack)          |
| `packages/web`      | Frontend admin UI (Nuxt 3, Vue 3, PrimeVue)                    |

For each affected scope:

1. Read `{scope}/CLAUDE.md` to understand its architecture and patterns
2. Search for related code with `Grep` and `Glob`
3. Read key files that will need modification
4. Note existing patterns the implementation should follow

## Step 3: Check Existing ADRs

```bash
ls docs/arc42/decisions/
```

Read any ADR that covers related technology choices. Flag if the implementation approach may need a new ADR (new
dependency, new framework, fundamental pattern change).

## Step 4: Identify Relevant Skills

Check if scaffold skills exist for the type of work needed:

- New agent → `/scaffold-agent`
- New pipeline → `/scaffold-pipeline`
- New process → `/scaffold-process`
- New API endpoint → `/scaffold-api-endpoint` + `/scaffold-api-service` + `/scaffold-api-repository`
- New frontend page → `/scaffold-frontend-page` + `/scaffold-composable`
- New bot handler → `/scaffold-bot-handler`
- New event type → `/validate-events` + `/nats-events`

Reference these in the plan so the implementer can invoke them.

## Step 5: Create the Plan

Structure the plan with these sections:

1. **Issue Summary** — one-sentence goal
2. **Affected Scopes** — which of the 7 scopes are touched and why
3. **Implementation Steps** — each step must reference:
   - Concrete file paths (not placeholders)
   - Existing pattern to follow (a real file in the codebase)
   - Relevant scaffold skill if applicable
4. **Cross-Scope Impact** — if `packages/core` changes, list downstream scopes that need testing
5. **Event System Impact** — new Control or Display events needed? Check `packages/core/swiss_ai_hub/core/events/`
6. **Testing Strategy** — which scopes need `make test`, new test files needed
7. **ADR Needed?** — yes/no with justification
8. **Risks** — ambiguities that need team input before starting

### Rules

- Every step must reference concrete files from the codebase, not placeholders
- Follow existing patterns — read the scope's CLAUDE.md before proposing new abstractions
- Identify step dependencies (what must happen first — typically `packages/core` before downstream scopes)
- If `packages/core` is modified, list all downstream scopes that import from it

## Troubleshooting

| Problem                       | Solution                                                       |
| ----------------------------- | -------------------------------------------------------------- |
| Issue not found               | Verify issue number: `gh issue list -R bbvch-ai/aihub-core`    |
| Issue is vague                | List what needs clarification, suggest asking the issue author |
| Spans too many scopes         | Break into sub-tasks, suggest splitting the issue              |
| No existing pattern to follow | Flag as risk — may need an ADR for the new pattern             |
| Sub-issues exist              | Use `get_sub_issues` to get the task breakdown                 |

## Done When

- Plan references concrete file paths from the codebase (no placeholders)
- All affected scopes identified with their CLAUDE.md consulted
- Relevant ADRs checked and referenced
- Applicable scaffold skills listed for the implementer
- Cross-scope dependencies mapped

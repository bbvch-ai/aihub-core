---
name: explain
description: Analyze and explain code in the swiss-ai-hub monorepo by reading the documentation hierarchy (README.md, CLAUDE.md, scope docs) and tracing cross-scope dependencies. Use when user says 'explain this code', 'what does this do', 'how does this work', 'walk me through', 'explain folder X', or 'help me understand'. Takes a file or folder path as argument. Do NOT use for code review (use /review-diff), deep codebase knowledge building (use codebase-expert agent), or documentation updates (use /update-doc).
allowed-tools: Read, Grep, Glob
---

# Explain Code - Analyze and Explain Any File or Folder

Explain the code at \$ARGUMENTS by reading the documentation hierarchy, analyzing structure, and tracing dependencies
across the swiss-ai-hub monorepo.

## Step 1: Identify the Scope

Determine which monorepo scope the target path belongs to:

| Scope               | Source root                                | Responsibility                                        |
| ------------------- | ------------------------------------------ | ----------------------------------------------------- |
| `packages/core`     | `packages/core/swiss_ai_hub/core/`         | Shared library (events, entities, NATS, auth, config) |
| `packages/api`      | `packages/api/swiss_ai_hub/api/`           | REST API + WebSocket (FastAPI)                        |
| `packages/agent`    | `packages/agent/swiss_ai_hub/agent/`       | AI agent workflows (LlamaIndex)                       |
| `packages/pipeline` | `packages/pipeline/swiss_ai_hub/pipeline/` | Data ingestion (Dagster)                              |
| `packages/process`  | `packages/process/swiss_ai_hub/process/`   | Business process orchestration                        |
| `packages/bot`      | `packages/bot/swiss_ai_hub/bot/`           | Bot integrations (Teams, Slack)                       |
| `packages/web`      | `packages/web/swiss_ai_hub_web/`           | Frontend admin UI (Nuxt 3)                            |

Note the double-nesting convention: `{scope}/{scope}/` where the outer directory is the package root and the inner
contains the source code.

## Step 2: Read the Documentation Hierarchy

Read docs from broad to narrow — each layer adds context:

1. `README.md` — project-wide architecture and services overview
2. `{scope}/README.md` — scope-level architecture, folder structure, patterns
3. `{scope}/CLAUDE.md` — coding conventions, key classes, essential files for that scope
4. README in the target directory itself (if it exists)
5. READMEs in parent directories between the scope root and the target

## Step 3: Analyze the Code in Context

Read the source files at \$ARGUMENTS and trace how they fit into the architecture:

- **Architectural layer**: Controller → Service → Entity? Event handler? Dagster asset? LlamaIndex workflow step?
- **Cross-scope dependencies**: Does it import from `packages/core`? Which shared classes does it use (events, entities,
  NATS subscribers, auth)?
- **Event system role**: Does it publish or subscribe to Control/Display events? Check
  `packages/core/swiss_ai_hub/core/events/` for the event hierarchy.
- **Entry points**: How is this code triggered? (API route registration in `main.py`, NATS subscription, Dagster asset
  materialization, bot handler registration)

## Step 4: Provide the Explanation

Structure the explanation as:

1. **Purpose** — what problem this solves and where it fits in the platform
2. **Key components** — main classes/files with their roles
3. **Data flow** — how requests/events flow through this code
4. **Dependencies** — what it imports from `packages/core` and other scopes
5. **Integration points** — how other parts of the system interact with it

## Examples

**Explain the API routes**:

```
/explain packages/api/swiss_ai_hub/api/routes/agent
```

Output: Explanation of the agent API controllers, services, DTOs, route registration, and how they connect to
`packages/core` entities.

**Explain an agent**:

```
/explain packages/agent/swiss_ai_hub/agent/agents/RagAgent
```

Output: Breakdown of the RAG agent workflow — events, config, LlamaIndex steps, and NATS integration.

**Explain a shared module**:

```
/explain packages/core/swiss_ai_hub/core/nats
```

Output: How the NATS abstraction layer works — subscribers, publishers, topic management, and the Swiss AI Agent
Protocol implementation.

## Troubleshooting

| Problem                    | Solution                                                    |
| -------------------------- | ----------------------------------------------------------- |
| Target path does not exist | Verify the path — check for typos or use Glob to find it    |
| No README in the hierarchy | Rely on scope CLAUDE.md and code analysis                   |
| Code is highly complex     | Break explanation into sections per file or component       |
| Scope unclear              | Check which `pyproject.toml` the path falls under           |
| Cross-scope imports        | Trace back to `packages/core` — all shared code lives there |

---
name: explain
description: Analyze and explain code in the aihub-core monorepo by reading the documentation hierarchy (README.md, CLAUDE.md, scope docs) and tracing cross-scope dependencies. Use when user says 'explain this code', 'what does this do', 'how does this work', 'walk me through', 'explain folder X', or 'help me understand'. Takes a file or folder path as argument. Do NOT use for code review (use /review-diff), deep codebase knowledge building (use codebase-expert agent), or documentation updates (use /update-doc).
allowed-tools: Read, Grep, Glob
---

# Explain Code - Analyze and Explain Any File or Folder

Explain the code at \$ARGUMENTS by reading the documentation hierarchy, analyzing structure, and tracing dependencies
across the aihub-core monorepo.

## Step 1: Identify the Scope

Determine which monorepo scope the target path belongs to:

| Scope            | Source root                      | Responsibility                                        |
| ---------------- | -------------------------------- | ----------------------------------------------------- |
| `aihub_lib`      | `aihub_lib/aihub_lib/`           | Shared library (events, entities, NATS, auth, config) |
| `aihub_api`      | `aihub_api/aihub_api/`           | REST API + WebSocket (FastAPI)                        |
| `aihub_agent`    | `aihub_agent/aihub_agent/`       | AI agent workflows (LlamaIndex)                       |
| `aihub_pipeline` | `aihub_pipeline/aihub_pipeline/` | Data ingestion (Dagster)                              |
| `aihub_process`  | `aihub_process/aihub_process/`   | Business process orchestration                        |
| `aihub_bot`      | `aihub_bot/aihub_bot/`           | Bot integrations (Teams, Slack)                       |
| `aihub_web`      | `aihub_web/aihub_web/`           | Frontend admin UI (Nuxt 3)                            |

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
- **Cross-scope dependencies**: Does it import from `aihub_lib`? Which shared classes does it use (events, entities,
  NATS subscribers, auth)?
- **Event system role**: Does it publish or subscribe to Control/Display events? Check `aihub_lib/aihub_lib/events/` for
  the event hierarchy.
- **Entry points**: How is this code triggered? (API route registration in `main.py`, NATS subscription, Dagster asset
  materialization, bot handler registration)

## Step 4: Provide the Explanation

Structure the explanation as:

1. **Purpose** — what problem this solves and where it fits in the platform
2. **Key components** — main classes/files with their roles
3. **Data flow** — how requests/events flow through this code
4. **Dependencies** — what it imports from `aihub_lib` and other scopes
5. **Integration points** — how other parts of the system interact with it

## Examples

**Explain the API routes**:

```
/explain aihub_api/aihub_api/routes/agent
```

Output: Explanation of the agent API controllers, services, DTOs, route registration, and how they connect to
`aihub_lib` entities.

**Explain an agent**:

```
/explain aihub_agent/aihub_agent/agents/RagAgent
```

Output: Breakdown of the RAG agent workflow — events, config, LlamaIndex steps, and NATS integration.

**Explain a shared module**:

```
/explain aihub_lib/aihub_lib/nats
```

Output: How the NATS abstraction layer works — subscribers, publishers, topic management, and the Swiss AI Agent
Protocol implementation.

## Troubleshooting

| Problem                    | Solution                                                 |
| -------------------------- | -------------------------------------------------------- |
| Target path does not exist | Verify the path — check for typos or use Glob to find it |
| No README in the hierarchy | Rely on scope CLAUDE.md and code analysis                |
| Code is highly complex     | Break explanation into sections per file or component    |
| Scope unclear              | Check which `pyproject.toml` the path falls under        |
| Cross-scope imports        | Trace back to `aihub_lib` — all shared code lives there  |

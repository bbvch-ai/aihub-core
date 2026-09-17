# Claude Code Configuration

This directory contains all Claude Code configuration for the swiss-ai-hub monorepo.

## Directory Structure

```
.claude/
├── settings.json          # Hooks, permissions, and project config
├── README.md              # This file
├── skills/                # Reusable workflow skills (invoke via /skill-name)
│   ├── create-pr/         # Pre-PR validation and creation
│   ├── update-doc/        # Documentation synchronization
│   ├── explain/           # Code analysis and explanation
│   ├── document-decision/ # ADR creation
│   ├── document-feature/  # Feature documentation
│   ├── implement-feedback-from-pr/ # PR feedback implementation
│   ├── scaffold-agent/    # Generate new AI agent
│   ├── scaffold-pipeline/ # Generate new Dagster pipeline
│   ├── scaffold-process/  # Generate new agentic process
│   ├── scaffold-api-endpoint/ # Generate new REST API endpoint
│   ├── scaffold-frontend-page/ # Generate new frontend page
│   ├── scaffold-bot-handler/ # Generate new bot integration
│   ├── lint/              # Format, lint, and type-check all scopes
│   ├── merge-main/        # Sync feature branch with main
│   ├── test-scope/        # Smart scoped test runner
│   ├── docker-dev/        # Docker environment management
│   ├── check-i18n/        # Internationalization validation
│   ├── generate-sdk/      # Frontend API SDK regeneration
│   ├── dependency-audit/  # Dependency health check
│   ├── validate-events/   # Event system validation
│   ├── debug-agent/       # Agent debugging assistant
│   ├── scaffold-composable/ # Generate Pinia-Colada composable
│   ├── scaffold-event-display/ # Generate event display component
│   ├── scaffold-dashboard-widget/ # Generate dashboard widget
│   ├── debug-frontend/    # Visual frontend debugging (Playwright)
│   ├── audit-frontend/    # Frontend code audit
│   ├── primevue-lookup/   # PrimeVue component docs lookup
│   ├── scaffold-frontend-subpage/ # Generate detail wrapper + tab subpages
│   ├── scaffold-frontend-component/ # Generate Vue component (card, modal, list, etc.)
│   ├── design-system/     # Design system reference guide
│   ├── scaffold-api-service/ # Generate API service layer
│   ├── scaffold-api-repository/ # Generate MongoEngine entity (schema + repository)
│   ├── api-auth-guide/    # Auth, identity, permissions reference
│   ├── nats-events/       # NATS, JetStream, events, pub/sub, RPC reference
│   ├── dagster-pipelines/ # Dagster assets, resources, IO managers, partitions reference
│   ├── rclone-guide/      # Rclone cloud storage integration reference
│   ├── debug-pipeline/    # Pipeline troubleshooting and debugging
│   ├── setup-bot-connection/ # Bot connection setup (Azure, Teams, Slack)
│   ├── debug-bot/         # Bot troubleshooting and debugging
│   ├── bot-reference/     # Bot architecture and patterns reference
│   ├── review-diff/       # Pre-PR code review (diff analysis)
│   ├── plan-issue/        # GitHub issue → implementation plan
│   └── reflect/           # Session retrospective → improve CLAUDE.md/skills
├── agents/                # Custom subagents with specialized roles
│   ├── codebase-expert.md # Deep knowledge builder (with memory)
│   ├── code-reviewer.md   # Quality and security reviewer
│   ├── event-flow-analyzer.md # Event system tracer (with memory)
│   ├── docker-ops.md      # Docker infrastructure expert
│   ├── test-analyzer.md   # Test coverage analyzer
│   ├── frontend-analyzer.md # Vue/Nuxt expert
│   └── documentation-keeper.md # Docs freshness tracker (with memory)
├── hooks/                 # Deterministic automation scripts
│   ├── auto-format-python.sh    # PostToolUse: Format Python on edit
│   ├── auto-format-frontend.sh  # PostToolUse: Format TS/Vue on edit
│   ├── protect-sensitive-files.sh # PreToolUse: Block secret access
│   ├── scope-boundary-check.sh  # PreToolUse: Warn cross-scope imports
│   ├── stop-hook-git-check.sh   # Stop: Check uncommitted changes
│   └── session-start.sh         # SessionStart: Install deps, check env
└── mcp/                   # Launcher scripts for the stdio MCP servers in .mcp.json
    ├── mcp-mongodb.sh     # Read-only database access (FerretDB/MongoDB)
    ├── mcp-postgres.sh    # Read-only PostgreSQL (one database at a time, POSTGRES_MCP_DB)
    ├── mcp-redis.sh       # Valkey: RunContext/ThreadContext agent state
    ├── mcp-milvus.sh      # Milvus vector DB (collections, search, indexes)
    ├── mcp-nats.sh        # NATS messaging (subjects, streams, monitoring)
    ├── mcp-dagster.sh     # Dagster pipelines (runs, assets, run logs, failure summaries)
    ├── mcp-sonarqube.sh   # SonarCloud issues and quality gates (needs SONARQUBE_TOKEN)
    ├── mcp-github.sh      # GitHub issues, PRs, code search (disabled; the skills use `gh`)
    ├── mcp-playwright.sh  # Browser automation and UI debugging
    ├── mcp-context7.sh    # Up-to-date library documentation lookup
    ├── mcp-primevue.sh    # PrimeVue component library (props, events, slots, theming)
    ├── mcp-likec4.sh      # LikeC4 architecture model (docs/likec4 workspace)
    ├── mcp-langfuse-headers.sh          # Basic-auth header for the langfuse HTTP server
    └── mcp-swiss-ai-hub-api-headers.sh  # Bearer header for the platform API HTTP server

`langfuse`, `nuxt` and `swiss_ai_hub_api` are configured directly as `"type": "http"` servers
rather than launcher scripts. The two that need credentials use `headersHelper`, because
`.mcp.json` expands `${VAR}` against the shell environment and so cannot read `.env`.
```

## Quick Reference

### Skills (43 total)

| Category       | Skill                          | Description                                        |
| -------------- | ------------------------------ | -------------------------------------------------- |
| Workflow       | `/review-diff`                 | Pre-PR code review (diff analysis)                 |
|                | `/create-pr`                   | Pre-PR validation orchestrator                     |
|                | `/implement-feedback-from-pr`  | Apply PR feedback                                  |
|                | `/plan-issue`                  | GitHub issue → implementation plan                 |
|                | `/reflect`                     | Session retrospective → improve CLAUDE.md/skills   |
|                | `/lint`                        | Format and lint all scopes                         |
|                | `/merge-main`                  | Sync feature branch with main                      |
|                | `/test-scope`                  | Scoped test runner                                 |
| Docs           | `/update-doc`                  | Sync docs, CLAUDE.md, and skills with code         |
|                | `/explain`                     | Analyze and explain code                           |
|                | `/document-decision`           | Create ADRs                                        |
|                | `/document-feature`            | Document features                                  |
| Scaffold       | `/scaffold-agent`              | New AI agent                                       |
|                | `/scaffold-pipeline`           | New Dagster pipeline                               |
|                | `/scaffold-process`            | New agentic process                                |
|                | `/scaffold-api-endpoint`       | New REST API controller                            |
|                | `/scaffold-api-service`        | New API service layer                              |
|                | `/scaffold-api-repository`     | New MongoEngine entity                             |
|                | `/scaffold-frontend-page`      | New frontend page                                  |
|                | `/scaffold-bot-handler`        | New bot handler                                    |
| DevEx          | `/docker-dev`                  | Docker env management                              |
|                | `/check-i18n`                  | Translation validation                             |
|                | `/generate-sdk`                | API SDK regeneration                               |
|                | `/dependency-audit`            | Dep health check                                   |
|                | `/validate-events`             | Event system validation                            |
|                | `/debug-agent`                 | Agent debugging                                    |
|                | `/debug-pipeline`              | Pipeline troubleshooting and debugging             |
| Frontend       | `/scaffold-composable`         | New Pinia-Colada composable                        |
|                | `/scaffold-event-display`      | New event display component                        |
|                | `/scaffold-dashboard-widget`   | New dashboard widget                               |
|                | `/debug-frontend`              | Visual UI debugging (Playwright)                   |
|                | `/audit-frontend`              | Frontend code audit                                |
|                | `/primevue-lookup`             | PrimeVue component docs                            |
|                | `/scaffold-frontend-subpage`   | New detail page with tabs                          |
|                | `/scaffold-frontend-component` | New Vue component (card, modal, list)              |
|                | `/design-system`               | Design system reference                            |
| API & Pipeline | `/api-auth-guide`              | Auth, identity, permissions reference              |
|                | `/nats-events`                 | NATS, JetStream, events, pub/sub, RPC              |
|                | `/dagster-pipelines`           | Dagster assets, resources, IO managers, partitions |
|                | `/rclone-guide`                | Rclone cloud storage integration                   |
| Bot            | `/setup-bot-connection`        | Bot connection setup (Azure, Teams, Slack)         |
|                | `/debug-bot`                   | Bot troubleshooting and debugging                  |
|                | `/bot-reference`               | Bot architecture and patterns reference            |

### Local Overrides (gitignored)

- `CLAUDE.local.md` — Personal preferences
- `.claude/settings.local.json` — Local settings
- `.claude/mcp.local.json` — Local MCP servers

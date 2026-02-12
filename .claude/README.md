# Claude Code Configuration

This directory contains all Claude Code configuration for the aihub-core monorepo.

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
│   ├── document-solution/ # Solution concept editing
│   ├── implement-feedback-from-pr/ # PR feedback implementation
│   ├── scaffold-agent/    # Generate new AI agent
│   ├── scaffold-pipeline/ # Generate new Dagster pipeline
│   ├── scaffold-process/  # Generate new agentic process
│   ├── scaffold-api-endpoint/ # Generate new REST API endpoint
│   ├── scaffold-frontend-page/ # Generate new frontend page
│   ├── scaffold-bot-handler/ # Generate new bot integration
│   ├── test-scope/        # Smart scoped test runner
│   ├── docker-dev/        # Docker environment management
│   ├── check-i18n/        # Internationalization validation
│   ├── generate-sdk/      # Frontend API SDK regeneration
│   ├── dependency-audit/  # Dependency health check
│   ├── validate-events/   # Event system validation
│   ├── debug-agent/       # Agent debugging assistant
│   ├── release-prep/      # Pre-release validation
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
│   └── api-auth-guide/    # Auth, identity, permissions reference
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
└── mcp/                   # Model Context Protocol server scripts (12 total)
    ├── mcp-mongodb.sh     # Read-only database access (FerretDB/MongoDB)
    ├── mcp-aihub-api.sh   # API endpoint testing
    ├── mcp-phoenix.sh     # AI observability and tracing
    ├── mcp-context7.sh    # Up-to-date library documentation lookup
    ├── mcp-playwright.sh  # Browser automation and UI debugging
    ├── mcp-github.sh      # GitHub issues, PRs, code search (needs PAT, disabled)
    ├── mcp-postgres.sh    # Read-only PostgreSQL access (infrastructure DBs)
    ├── mcp-primevue.sh    # PrimeVue component library (props, events, slots, theming)
    ├── mcp-nuxt.sh        # Nuxt framework docs and guides (official remote)
    ├── mcp-milvus.sh      # Milvus vector DB (collections, search, indexes)
    ├── mcp-nats.sh        # NATS messaging (subjects, streams, monitoring)
    └── mcp-dagster.sh     # Dagster pipelines (runs, assets, jobs)
```

## Quick Reference

### Skills (33 total)

| Category | Skill | Description |
|----------|-------|-------------|
| Docs | `/create-pr` | Pre-PR validation |
| | `/update-doc` | Sync docs with code |
| | `/explain` | Analyze and explain code |
| | `/document-decision` | Create ADRs |
| | `/document-feature` | Document features |
| | `/document-solution` | Edit solution concepts |
| | `/implement-feedback-from-pr` | Apply PR feedback |
| Scaffold | `/scaffold-agent` | New AI agent |
| | `/scaffold-pipeline` | New Dagster pipeline |
| | `/scaffold-process` | New agentic process |
| | `/scaffold-api-endpoint` | New REST API controller |
| | `/scaffold-api-service` | New API service layer |
| | `/scaffold-api-repository` | New MongoEngine entity |
| | `/scaffold-frontend-page` | New frontend page |
| | `/scaffold-bot-handler` | New bot handler |
| DevEx | `/test-scope` | Scoped test runner |
| | `/docker-dev` | Docker env management |
| | `/check-i18n` | Translation validation |
| | `/generate-sdk` | API SDK regeneration |
| | `/dependency-audit` | Dep health check |
| | `/validate-events` | Event system validation |
| | `/debug-agent` | Agent debugging |
| | `/release-prep` | Pre-release validation |
| Frontend | `/scaffold-composable` | New Pinia-Colada composable |
| | `/scaffold-event-display` | New event display component |
| | `/scaffold-dashboard-widget` | New dashboard widget |
| | `/debug-frontend` | Visual UI debugging (Playwright) |
| | `/audit-frontend` | Frontend code audit |
| | `/primevue-lookup` | PrimeVue component docs |
| | `/scaffold-frontend-subpage` | New detail page with tabs |
| | `/scaffold-frontend-component` | New Vue component (card, modal, list) |
| | `/design-system` | Design system reference |
| API | `/api-auth-guide` | Auth, identity, permissions reference |

### Local Overrides (gitignored)

- `CLAUDE.local.md` — Personal preferences
- `.claude/settings.local.json` — Local settings
- `.claude/mcp.local.json` — Local MCP servers

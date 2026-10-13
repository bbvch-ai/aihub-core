# Claude Code Configuration

This directory contains all Claude Code configuration for the swiss-ai-hub monorepo.

## Directory Structure

```
.claude/
├── settings.json          # Hooks, permissions, and project config
├── README.md              # This file
├── skills/                # Reusable workflow skills (invoke via /skill-name)
│   ├── create-pr/         # Pre-PR validation and creation
│   ├── pr-demo-video/     # Demo section from a screen recording on the linked issue
│   ├── review-diff/       # Pre-PR code review (diff analysis)
│   ├── implement-feedback-from-pr/ # PR feedback implementation
│   ├── lint/              # Format, lint, and type-check all scopes
│   ├── merge-main/        # Sync feature branch with main
│   ├── test-scope/        # Smart scoped test runner
│   ├── plan-issue/        # GitHub issue → implementation plan
│   ├── write-issue/       # Author a convention-conformant GitHub issue
│   ├── splice-issue/      # Split a large issue into sub-issues with blocked-by links
│   ├── reflect/           # Session retrospective → improve CLAUDE.md/skills
│   ├── update-doc/        # Documentation synchronization
│   ├── sync-agent-docs/   # Agent docs pages vs implementation
│   ├── write-doc/         # New VitePress docs page
│   ├── document-feature/  # Feature documentation
│   ├── document-decision/ # ADR creation
│   ├── arc42/             # arc42 chapter authoring
│   ├── likec4-dsl/        # LikeC4 DSL and CLI syntax
│   ├── explain/           # Code analysis and explanation
│   ├── create-or-audit-claude-md/ # Build or audit a CLAUDE.md
│   ├── create-or-audit-skill/ # Build or audit a skill
│   ├── create-or-audit-subagent/ # Build or audit a subagent
│   ├── docker-dev/        # Docker environment management
│   ├── generate-sdk/      # Frontend API SDK regeneration
│   ├── verify-sdk-sync/   # Check committed SDK client against the backend
│   ├── i18n/              # i18n reference and validation
│   ├── scaffold-agent/    # Generate new AI agent
│   ├── scaffold-pipeline/ # Generate new Dagster pipeline
│   ├── scaffold-api-endpoint/ # Generate new REST API endpoint
│   ├── scaffold-api-service/ # Generate API service layer
│   ├── scaffold-api-repository/ # Generate MongoEngine entity (schema + repository)
│   ├── scaffold-bot-handler/ # Generate new bot integration
│   ├── scaffold-frontend-page/ # Generate new frontend page
│   ├── scaffold-frontend-subpage/ # Generate detail wrapper + tab subpages
│   ├── scaffold-frontend-component/ # Generate Vue component (card, modal, list, etc.)
│   ├── scaffold-composable/ # Generate Pinia-Colada composable
│   ├── scaffold-event-display/ # Generate event display component
│   ├── debug-agent/       # Agent debugging assistant
│   ├── debug-pipeline/    # Pipeline troubleshooting and debugging
│   ├── debug-frontend/    # Visual frontend debugging (Playwright)
│   ├── audit-frontend/    # Frontend code audit
│   ├── primevue-lookup/   # PrimeVue component docs lookup
│   ├── design-system/     # Design system reference guide
│   ├── nats-events/       # NATS, JetStream, events, pub/sub, RPC reference
│   ├── dagster-pipelines/ # Dagster assets, resources, IO managers, partitions reference
│   ├── rclone-guide/      # Rclone source pipeline reference
│   ├── bot-framework/     # Bot architecture, patterns, and troubleshooting reference
│   └── setup-bot-connection/ # Bot connection setup (Azure, Teams, Slack)
├── agents/                # Custom subagents with specialized roles
│   ├── architect.md       # Architectural implications and code placement
│   ├── impact-analyzer.md # Cross-package blast radius of core changes
│   ├── scope-wiring-checker.md # End-to-end wiring (discovery, display, forms, i18n)
│   ├── test-gap-analyzer.md # Untested code paths
│   ├── deployment-reviewer.md # Docker Compose and infra review
│   ├── connectivity-researcher.md # Outbound connectivity of one application container
│   ├── docs-researcher.md # Up-to-date library docs via MCP
│   └── doc-sync.md        # Documentation synchronization
├── output-styles/         # Response styles (architect-please-explain, business, marketing)
├── statusline.sh          # Status line script
├── hooks/                 # Deterministic automation scripts
│   ├── auto-format-python.sh    # PostToolUse: Format Python on edit
│   ├── auto-format-frontend.sh  # PostToolUse: Format TS/Vue on edit
│   ├── auto-format-markdown.sh  # PostToolUse: Format Markdown on edit
│   ├── auto-format-yaml.sh      # PostToolUse: Format YAML on edit
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
    ├── mcp-playwright.sh  # Browser automation and UI debugging
    ├── mcp-context7.sh    # Up-to-date library documentation lookup
    ├── mcp-primevue.sh    # PrimeVue component library (props, events, slots, theming)
    ├── mcp-likec4.sh      # LikeC4 architecture model (docs/likec4 workspace)
    ├── mcp-langfuse-headers.sh          # Basic-auth header for the langfuse HTTP server
    └── mcp-swiss-ai-hub-api-headers.sh  # Bearer header for the platform API HTTP server

`langfuse`, `nuxt` and `swiss_ai_hub_api` are configured directly as `"type": "http"` servers
rather than launcher scripts. The two that need credentials use `headersHelper`, because
`.mcp.json` expands `${VAR}` against the shell environment and so cannot read `.env`.

There is deliberately no GitHub MCP server: the `gh` CLI already reaches every endpoint it
wraps (including code scanning, Dependabot, sub-issues and rulesets, which have no dedicated
`gh` subcommand but work through `gh api`), infers the repo from the git remote, and reuses
the token `gh auth login` already stored — so the MCP would only add a second long-lived PAT
on disk. The skills use `gh` throughout.
```

## MCP Server Environment Keys

**Read this first if an MCP server fails to connect on a fresh clone.** `.env` is gitignored, so it does not travel with
the repo — `cp .env.dev .env` gives you every key the stack needs, but the MCP-only keys below arrive commented out and
must be filled in by hand. A missing key shows up as a bare `CONNECTION_CLOSED`, which says nothing about the cause.

MCP servers connect **at session start only**. Restart Claude Code after editing `.env`.

### Keys used only by MCP servers

Nothing in `infra/` or `packages/` reads these. They live in a marked block at the bottom of `.env` and `.env.dev`.

| Key                     | Server      | Required?                                   | How to get it                                                                                                                                                                   |
| ----------------------- | ----------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `SONARQUBE_TOKEN`       | `sonarqube` | **Yes** — the server exits without it       | SonarCloud → My Account → Security → Generate Token, type "User Token". Works with GitHub SSO login. **Expires — 30 days by default**, after which calls fail with auth errors. |
| `POSTGRES_MCP_DB`       | `postgres`  | No — defaults to `openwebui`                | Pick one of `openwebui` / `langfuse` / `dagster` / `litellm` / `keycloak` / `admin`. PostgreSQL cannot query across databases, so the server sees exactly one at a time.        |
| `CONTEXT7_API_KEY`      | `context7`  | No — works anonymously                      | Free key at <https://context7.com/dashboard> for higher rate limits.                                                                                                            |
| `SONARQUBE_ORG`         | `sonarqube` | No — defaults to `bbv-ai`                   | Only for a different SonarCloud organisation.                                                                                                                                   |
| `DAGSTER_WEBSERVER_URL` | `dagster`   | No — defaults to `http://localhost:3000`    | Only if Dagster runs elsewhere.                                                                                                                                                 |
| `DAGSTER_READ_ONLY`     | `dagster`   | No — read-only by default (17 tools)        | Set `false` to expose all 27 tools, including run launching and asset wiping.                                                                                                   |
| `REDIS_MCP_URL`         | `redis`     | No — built from `REDIS_URL` + `REDIS_TOKEN` | Only to point at a different Redis, e.g. a read-only ACL user.                                                                                                                  |

### Stack keys the MCP servers reuse

These already come from `.env.dev`, so they need no extra setup — listed so you know which server breaks if one is
wrong.

| Server             | Keys                                                                   |
| ------------------ | ---------------------------------------------------------------------- |
| `postgres`         | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`, `POSTGRES_HOST` |
| `mongodb`          | `MONGO_USERNAME`, `MONGO_PASSWORD`                                     |
| `redis`            | `REDIS_URL`, `REDIS_TOKEN`                                             |
| `milvus`           | `MILVUS_URL`, `MILVUS_ROOT_PASSWORD`, `MILVUS_TOKEN`                   |
| `nats`             | `NATS_ENDPOINT` (or `NATS_URL`), `NATS_TOKEN`                          |
| `langfuse`         | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`                           |
| `swiss_ai_hub_api` | `SUPERUSER_TOKEN`                                                      |

`likec4`, `playwright`, `primevue` and `nuxt` need no environment keys at all.

### Host tools and running services

Keys are not the only prerequisite. The SessionStart hook warns about missing host tools, but does not install them:

- `pipx` — required by `milvus`
- `unzip` — required by `nats` (it downloads and caches the `nats` CLI into `.claude/mcp/bin/`)
- Docker dev stack up — `mongodb`, `postgres`, `redis`, `milvus`, `nats`, `langfuse`
- Started separately — `dagster` (`make document-ingestion-pipeline` in `packages/pipeline`, :3000) and
  `swiss_ai_hub_api` (`make run-dev` in `packages/api`, :8000)

## Quick Reference

### Skills (48 total)

| Category       | Skill                          | Description                                        |
| -------------- | ------------------------------ | -------------------------------------------------- |
| Workflow       | `/review-diff`                 | Pre-PR code review (diff analysis)                 |
|                | `/create-pr`                   | Pre-PR validation orchestrator                     |
|                | `/pr-demo-video`               | Demo section from a screen recording               |
|                | `/implement-feedback-from-pr`  | Apply PR feedback                                  |
|                | `/plan-issue`                  | GitHub issue → implementation plan                 |
|                | `/write-issue`                 | Author a new GitHub issue                          |
|                | `/splice-issue`                | Split a large issue into sub-issues                |
|                | `/reflect`                     | Session retrospective → improve CLAUDE.md/skills   |
|                | `/lint`                        | Format and lint all scopes                         |
|                | `/merge-main`                  | Sync feature branch with main                      |
|                | `/test-scope`                  | Scoped test runner                                 |
| Docs           | `/update-doc`                  | Sync docs, CLAUDE.md, and skills with code         |
|                | `/sync-agent-docs`             | Sync an agent's docs page with its implementation  |
|                | `/write-doc`                   | New VitePress docs page                            |
|                | `/document-feature`            | Document features                                  |
|                | `/document-decision`           | Create ADRs                                        |
|                | `/arc42`                       | arc42 architecture chapters                        |
|                | `/likec4-dsl`                  | LikeC4 DSL and CLI syntax                          |
|                | `/explain`                     | Analyze and explain code                           |
| Meta           | `/create-or-audit-claude-md`   | Build or audit a CLAUDE.md                         |
|                | `/create-or-audit-skill`       | Build or audit a skill                             |
|                | `/create-or-audit-subagent`    | Build or audit a subagent                          |
| Scaffold       | `/scaffold-agent`              | New AI agent                                       |
|                | `/scaffold-pipeline`           | New Dagster pipeline                               |
|                | `/scaffold-api-endpoint`       | New REST API controller                            |
|                | `/scaffold-api-service`        | New API service layer                              |
|                | `/scaffold-api-repository`     | New MongoEngine entity                             |
|                | `/scaffold-frontend-page`      | New frontend page                                  |
|                | `/scaffold-bot-handler`        | New bot handler                                    |
| DevEx          | `/docker-dev`                  | Docker env management                              |
|                | `/i18n`                        | i18n reference and validation                      |
|                | `/generate-sdk`                | API SDK regeneration                               |
|                | `/verify-sdk-sync`             | Check committed SDK against the backend            |
|                | `/debug-agent`                 | Agent debugging                                    |
|                | `/debug-pipeline`              | Pipeline troubleshooting and debugging             |
| Frontend       | `/scaffold-composable`         | New Pinia-Colada composable                        |
|                | `/scaffold-event-display`      | New event display component                        |
|                | `/scaffold-frontend-subpage`   | New detail page with tabs                          |
|                | `/scaffold-frontend-component` | New Vue component (card, modal, list)              |
|                | `/debug-frontend`              | Visual UI debugging (Playwright)                   |
|                | `/audit-frontend`              | Frontend code audit                                |
|                | `/primevue-lookup`             | PrimeVue component docs                            |
|                | `/design-system`               | Design system reference                            |
| API & Pipeline | `/nats-events`                 | NATS, JetStream, events, pub/sub, RPC              |
|                | `/dagster-pipelines`           | Dagster assets, resources, IO managers, partitions |
|                | `/rclone-guide`                | Rclone source pipeline                             |
| Bot            | `/setup-bot-connection`        | Bot connection setup (Azure, Teams, Slack)         |
|                | `/bot-framework`               | Bot architecture, patterns, troubleshooting        |

### Local Overrides (gitignored)

- `CLAUDE.local.md` — Personal preferences
- `.claude/settings.local.json` — Local settings
- `.claude/mcp.local.json` — Local MCP servers

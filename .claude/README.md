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
│   └── release-prep/      # Pre-release validation
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
└── mcp/                   # Model Context Protocol server scripts
    ├── mcp-mongodb.sh     # Read-only database access
    ├── mcp-aihub-api.sh   # API endpoint testing
    └── mcp-phoenix.sh     # AI observability and tracing
```

## Quick Reference

### Skills (21 total)

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
| | `/scaffold-api-endpoint` | New REST endpoint |
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

### Local Overrides (gitignored)

- `CLAUDE.local.md` — Personal preferences
- `.claude/settings.local.json` — Local settings
- `.claude/mcp.local.json` — Local MCP servers

# Plan: SOTA Claude Code Enablement for aihub-core

## Vision

Transform aihub-core from "good CLAUDE.md files + 7 legacy commands" into a **showcase
reference implementation** of how an enterprise monorepo should be Claude Code enabled.
Every common developer workflow — scaffolding agents, debugging events, managing Docker,
running scoped tests, reviewing PRs, writing docs — gets a dedicated skill, agent, or hook.

---

## Current State Summary

**What exists:**
- 10 AGENTS.md files (excellent progressive disclosure hierarchy)
- 7 legacy slash commands in `.claude/commands/` (no frontmatter, no model-invocation)
- 2 MCP servers (MongoDB read-only, AI-Hub API)
- 1 global Stop hook (git hygiene check)
- Minimal `.claude/settings.json` (1 setting: `includeCoAuthoredBy: false`)
- No `.claude/skills/`, `.claude/agents/`, `.claude/hooks/` directories

**What's missing for SOTA:**
- No scaffolding skills for the platform's core abstractions (agents, pipelines, processes, API endpoints, frontend pages)
- No custom subagents for specialized tasks (code review, event tracing, Docker ops, testing)
- No project-level hooks (no auto-format, no security guards, no session setup)
- No MCP for Phoenix observability (already referenced in AGENTS.md but not configured)
- No pre-commit configuration
- No `.gitignore` entries for Claude local files
- Legacy commands lack frontmatter (no model-invocation, no tool scoping)
- No developer experience skills (docker management, i18n validation, SDK generation, dependency audit)

---

## Phase 1: Foundation — Hooks & Settings (Week 1)

Deterministic guardrails that enforce quality automatically. These benefit every
subsequent phase because all future work goes through these gates.

### 1.1 Create `.claude/hooks/` directory with 6 hook scripts

#### Hook 1: `auto-format-python.sh` (PostToolUse → Edit|Write)
- Detect if edited file is Python (`.py`)
- Determine which scope the file belongs to (parse path for aihub_lib, aihub_agent, etc.)
- Run `poetry run ruff format <file>` + `poetry run ruff check --fix <file>` within that scope
- Exit 0 always (formatting is best-effort, should never block Claude)
- Handles edge case: file outside any scope (skip formatting)

#### Hook 2: `auto-format-frontend.sh` (PostToolUse → Edit|Write)
- Detect if edited file is TypeScript/Vue (`.ts`, `.vue`, `.tsx`)
- Run `npx eslint --fix <file>` within aihub_web/aihub_web/
- Exit 0 always

#### Hook 3: `protect-sensitive-files.sh` (PreToolUse → Edit|Write|Read)
- Parse tool input for file path
- Block access to patterns: `*.env*`, `*/certs/*`, `*credentials*`, `*secret*`,
  `*.pem`, `*.key`, `*_TOKEN*` files, `poetry.lock` (prevent manual edits)
- Exit 2 with descriptive message if blocked
- Exit 0 otherwise

#### Hook 4: `stop-hook-git-check.sh` (Stop)
- Port existing `/root/.claude/stop-hook-git-check.sh` to project level
- Same functionality: check uncommitted changes, untracked files, unpushed commits
- Register in project `.claude/settings.json` (portable with repo)

#### Hook 5: `session-start.sh` (SessionStart)
- Detect environment: check `$CLAUDE_CODE_REMOTE` for web vs local
- For web sessions (async mode to reduce startup latency):
  - Install Poetry if missing
  - Run `poetry install` in each Python scope
  - Run `pnpm install` in aihub_web/aihub_web/
  - Copy `.env.dev` to `.env` if `.env` missing
- For all sessions:
  - Print current git branch and status summary
  - Warn if on main branch (should be on feature branch)
  - Check if Docker dev stack is running (quick `docker compose ps` check)

#### Hook 6: `scope-boundary-check.sh` (PreToolUse → Edit|Write)
- Parse file path to determine target scope
- Check if the edit introduces imports from other scopes that bypass aihub_lib
  (e.g., aihub_api importing directly from aihub_agent — violation)
- Warn (stderr message, exit 0) but don't block — just make Claude aware
- Exception: aihub_process is allowed to import aihub_agent (documented dev dependency)

### 1.2 Enhanced `.claude/settings.json`

Expand from 1 setting to full configuration:

```json
{
  "includeCoAuthoredBy": false,
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/auto-format-python.sh" },
          { "type": "command", "command": ".claude/hooks/auto-format-frontend.sh" }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write|Read",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/protect-sensitive-files.sh" }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/scope-boundary-check.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/stop-hook-git-check.sh" }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/session-start.sh" }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "Bash(make *)",
      "Bash(poetry run *)",
      "Bash(poetry install)",
      "Bash(poetry add *)",
      "Bash(pnpm *)",
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git branch *)",
      "Bash(git stash *)",
      "Bash(gh pr *)",
      "Bash(gh issue *)",
      "Bash(docker compose -f docker-compose.dev.yml *)",
      "Bash(docker compose ps *)",
      "Bash(docker logs *)",
      "Skill"
    ]
  }
}
```

### 1.3 `.gitignore` additions

```
CLAUDE.local.md
.claude/settings.local.json
.claude/mcp.local.json
```

### 1.4 `CLAUDE.local.md` template

Create `.claude/CLAUDE.local.md.template` as a documented starting point:
```markdown
# Personal Claude Code Overrides
# Copy this to CLAUDE.local.md (gitignored) for local preferences.
#
# Example overrides:
# - Preferred model for subagents
# - Personal coding style preferences
# - Additional context about your local environment
```

---

## Phase 2: Migrate Legacy Commands to Skills (Week 1-2)

Move all 7 commands from `.claude/commands/` to `.claude/skills/` with proper
SKILL.md frontmatter, then delete the commands directory.

### Migration for each command:

#### 2.1 `create-pr` → `.claude/skills/create-pr/SKILL.md`
```yaml
---
name: create-pr
description: Pre-pull request validation and preparation. Run formatting, linting,
  type checking, and tests across all affected scopes before creating a PR.

allowed-tools: Bash, Read, Grep, Glob, Edit
---
```
- Preserve existing 237 lines of instructions
- User-invocable only (side-effects: git operations, gh CLI)

#### 2.2 `update-doc` → `.claude/skills/update-doc/SKILL.md`
```yaml
---
name: update-doc
description: Synchronize documentation with code changes. Update READMEs, docstrings,
  and architecture docs when code has changed. Use when documentation may be stale.
allowed-tools: Read, Grep, Glob, Edit, Write
---
```
- Model-invocable (Claude can auto-suggest when docs drift after code changes)

#### 2.3 `explain` → `.claude/skills/explain/SKILL.md`
```yaml
---
name: explain
description: Analyze and explain a specific part of the codebase. Creates or updates
  documentation based on code analysis. Use when asked to explain code.
allowed-tools: Read, Grep, Glob
---
```
- Model-invocable (read-only, advisory)

#### 2.4 `document-decision` → `.claude/skills/document-decision/SKILL.md`
```yaml
---
name: document-decision
description: Create an Architecture Decision Record (ADR) for significant technical
  decisions. Use when adding major dependencies, new frameworks, or altering patterns.

allowed-tools: Read, Grep, Glob, Write, Bash
---
```

#### 2.5 `document-feature` → `.claude/skills/document-feature/SKILL.md`
```yaml
---
name: document-feature
description: Create user-facing feature documentation following VitePress standards.
  Generates structured docs with setup, configuration, and examples.

allowed-tools: Read, Grep, Glob, Write
---
```

#### 2.6 `document-solution` → `.claude/skills/document-solution/SKILL.md`
```yaml
---
name: document-solution
description: Edit solution concept documentation for public-sector procurement
  evaluators. Targets neutral, verifiable prose.

allowed-tools: Read, Edit, Grep
---
```

#### 2.7 `implement-feedback-from-pr` → `.claude/skills/implement-feedback-from-pr/SKILL.md`
```yaml
---
name: implement-feedback-from-pr
description: Systematically implement feedback from PR reviews. Categorizes human
  vs bot feedback and handles each type appropriately.

allowed-tools: Bash, Read, Edit, Grep, Glob
---
```

### 2.8 Delete `.claude/commands/` directory after migration

---

## Phase 3: Platform Scaffolding Skills (Week 2-3)

These are entirely new skills that encode the platform's development patterns into
reusable, one-command workflows. Each eliminates significant boilerplate.

### 3.1 `scaffold-agent` — Generate complete AI agent boilerplate

**Location**: `.claude/skills/scaffold-agent/SKILL.md`

```yaml
---
name: scaffold-agent
description: Scaffold a new AI agent with all required boilerplate. Generates the
  agent class, events, config with form duality, test runner setup, BDD feature
  file, trigger.py, run.py, and Dockerfile. Use when creating a new agent.

allowed-tools: Read, Write, Bash, Grep, Glob
---
```

**What it generates** (based on patterns discovered in aihub_agent):
1. Agent class inheriting from `Agent` with `@step` decorated methods
2. Custom events (StartEvent, StopEvent) following BaseEvent hierarchy
3. AgentConfig with form duality (`as_form()` factory method)
4. StepConfig subclasses if agent has configurable steps
5. `trigger.py` for one-shot testing
6. `run.py` for interactive development
7. `tests/` directory with:
   - BDD `.feature` file with happy path scenario
   - Step implementation file using `AgentTestRunner`
   - `@async_test` decorator integration
8. `Dockerfile` following multi-stage build pattern
9. Entry in playground for Dagster-compatible debugging
10. README.md for the agent

**Supporting files**: Include reference to existing playground patterns
(`/aihub_agent/playground/minimal_workflow/`) as templates.

### 3.2 `scaffold-pipeline` — Generate Dagster pipeline boilerplate

**Location**: `.claude/skills/scaffold-pipeline/SKILL.md`

```yaml
---
name: scaffold-pipeline
description: Scaffold a new Dagster data pipeline with asset factory, I/O manager,
  resources, and ops. Generates the two-stage pipeline pattern used in aihub_pipeline.

allowed-tools: Read, Write, Bash, Grep, Glob
---
```

**What it generates** (based on aihub_pipeline patterns):
1. Asset factory in `assets/factories/<domain>/`
2. I/O manager in `io/<domain>/`
3. Resources in `resources/<domain>/`
4. Ops in `ops/<domain>/`
5. Playground integration (`playground/__init__.py` update)
6. Two-stage pattern: Source-specific ingestion → unified processing
7. DataVersion tracking for change detection
8. Partition definition for per-document processing
9. README.md for the pipeline

### 3.3 `scaffold-process` — Generate process orchestration boilerplate

**Location**: `.claude/skills/scaffold-process/SKILL.md`

```yaml
---
name: scaffold-process
description: Scaffold a new agentic process with entity delegation, work events,
  and process steps. Generates the orchestration pattern connecting agents, humans,
  and external programs.

allowed-tools: Read, Write, Bash, Grep, Glob
---
```

**What it generates** (based on aihub_process patterns):
1. AgenticProcess class with `@process_step` methods
2. WorkEvent / WorkRequestEvent subclasses per entity type
3. Entity delegation annotations (Agent.In/Out, Human.In/Out, Program.In/Out)
4. ProcessConfig with form duality
5. Human-in-the-loop form groups (FormKit elements)
6. BDD `.feature` file with delegation scenarios
7. Step implementation using `ProcessTestRunner`
8. README.md for the process

### 3.4 `scaffold-api-endpoint` — Generate API endpoint boilerplate

**Location**: `.claude/skills/scaffold-api-endpoint/SKILL.md`

```yaml
---
name: scaffold-api-endpoint
description: Scaffold a new REST API endpoint with Controller, Service, DTO, and
  test setup. Follows the fluent API pattern used in aihub_api.

allowed-tools: Read, Write, Bash, Grep, Glob
---
```

**What it generates** (based on aihub_api patterns):
1. Controller class with fluent API (`def create_resource(self) -> Self:`)
2. Service class with `@staticmethod @trace_fn` methods
3. Request/Response DTOs (Pydantic BaseModel)
4. Permission template (`aihub.user.<resource>.?>`)
5. Mount instruction for `app/main.py`
6. Test setup using `ApiTestRunner` + `AsyncClient`
7. i18n keys for all 4 locales (de, en, fr, it)
8. SDK regeneration reminder (`pnpm generate-sdk`)

### 3.5 `scaffold-frontend-page` — Generate Nuxt page boilerplate

**Location**: `.claude/skills/scaffold-frontend-page/SKILL.md`

```yaml
---
name: scaffold-frontend-page
description: Scaffold a new frontend page with composable, list/detail pages, and
  PrimeVue components. Follows the Pinia-Colada query pattern used in aihub_web.

allowed-tools: Read, Write, Bash, Grep, Glob
---
```

**What it generates** (based on aihub_web patterns):
1. Query composable (`composables/<service>/use<Service>.ts`) with Pinia-Colada
2. Mutation composable (`composables/<service>/useCreate<Service>.ts`)
3. List page (`pages/service/<service>.vue`) with StructuralColumn
4. Detail page (`pages/service/<service>/[id].vue`)
5. Card component (`components/<Service>/Card.vue`) with PrimeVue
6. i18n entries in all 4 locale files
7. SDK import references

### 3.6 `scaffold-bot-handler` — Generate bot integration boilerplate

**Location**: `.claude/skills/scaffold-bot-handler/SKILL.md`

```yaml
---
name: scaffold-bot-handler
description: Scaffold a new bot conversation handler for MS Teams or Slack.
  Generates ChatBot subclass with completion handler and conversation management.

allowed-tools: Read, Write, Bash, Grep, Glob
---
```

**What it generates** (based on aihub_bot patterns):
1. ChatBot subclass extending `BaseChatBot`
2. CompletionHandler for response generation
3. Channel-specific message formatting
4. ConversationEntity TTL configuration
5. Webhook route registration
6. Bot Framework Emulator test configuration

---

## Phase 4: Developer Experience Skills (Week 3-4)

Skills for daily development workflows that don't involve scaffolding.

### 4.1 `test-scope` — Smart scoped test runner

**Location**: `.claude/skills/test-scope/SKILL.md`

```yaml
---
name: test-scope
description: Identify which scopes are affected by current changes and run their
  tests. Parses git diff to determine affected scopes. Use after making code changes
  to verify nothing is broken.
allowed-tools: Bash, Read, Grep, Glob
---
```

**Logic**:
1. Run `git diff --name-only` to find changed files
2. Map files to scopes (aihub_lib → aihub_agent → aihub_api, etc.)
3. Include downstream scopes (changes to aihub_lib affect all consumers)
4. Run `make test` in each affected scope (in dependency order)
5. Report results with pass/fail per scope
6. If aihub_lib changed, warn that all downstream scopes need testing

### 4.2 `docker-dev` — Development environment management

**Location**: `.claude/skills/docker-dev/SKILL.md`

```yaml
---
name: docker-dev
description: Manage the Docker development environment. Start, stop, check health,
  view logs, and troubleshoot services. Use when working with the Docker stack.

allowed-tools: Bash, Read
---
```

**Capabilities**:
- `$ARGUMENTS = up`: Start dev stack (`docker compose -f docker-compose.dev.yml up -d`)
- `$ARGUMENTS = down`: Stop dev stack
- `$ARGUMENTS = health`: Check all service health statuses, report unhealthy
- `$ARGUMENTS = logs <service>`: Tail logs for a specific service
- `$ARGUMENTS = restart <service>`: Restart a specific service
- `$ARGUMENTS = ports`: Show all service URLs and ports
- `$ARGUMENTS = status`: Show running containers with resource usage

### 4.3 `check-i18n` — Internationalization validation

**Location**: `.claude/skills/check-i18n/SKILL.md`

```yaml
---
name: check-i18n
description: Validate that all 4 locale files (de, en, fr, it) have matching keys.
  Identifies missing translations and orphaned keys. Use after adding UI text.
allowed-tools: Read, Bash, Grep, Glob
---
```

**Logic**:
1. Parse all 4 YAML locale files (`aihub_web/aihub_web/i18n/locales/{de,en,fr,it}.yaml`)
2. Extract all key paths recursively
3. Compare key sets across languages
4. Report: missing keys per language, orphaned keys, total coverage percentage
5. Also check backend i18n (`aihub_lib/aihub_lib/i18n/`, `aihub_api/aihub_api/i18n/`)
6. Check LocaleString completeness in agents (all 4 locales for name/description)

### 4.4 `generate-sdk` — API SDK regeneration

**Location**: `.claude/skills/generate-sdk/SKILL.md`

```yaml
---
name: generate-sdk
description: Regenerate the frontend API SDK from the OpenAPI specification.
  Checks if the API server is running, starts it if needed, then generates.

allowed-tools: Bash, Read
---
```

**Logic**:
1. Check if API is running at http://localhost:8000
2. If not, warn user to start it (or offer to run `make run-dev` in background)
3. Run `cd aihub_web/aihub_web && pnpm generate-sdk`
4. Report generated/changed files
5. Run `pnpm lint` to fix any formatting issues

### 4.5 `dependency-audit` — Dependency health check

**Location**: `.claude/skills/dependency-audit/SKILL.md`

```yaml
---
name: dependency-audit
description: Audit Python and Node.js dependencies for outdated packages,
  vulnerabilities, and version constraint issues across all scopes.

allowed-tools: Bash, Read, Grep, Glob
---
```

**Logic**:
1. For each Python scope: `poetry show --outdated`
2. For frontend: `pnpm outdated`
3. Check for known vulnerabilities: `poetry audit` (if available) or `pip-audit`
4. Compare `aihub_lib` version tags across all scopes (detect version drift)
5. Flag pinned versions that could be relaxed
6. Flag over-broad constraints that risk breakage
7. Report summary with risk assessment

### 4.6 `validate-events` — Event system health check

**Location**: `.claude/skills/validate-events/SKILL.md`

```yaml
---
name: validate-events
description: Validate the event hierarchy, registration, and usage across
  the platform. Checks that all events are properly registered, serializable,
  and have matching subscribers. Use when modifying the event system.
allowed-tools: Read, Grep, Glob
---
```

**Logic**:
1. Find all BaseEvent subclasses across all scopes
2. Verify each has `_event_name` set (auto-registration)
3. Check ControlEvent vs DisplayEvent classification
4. For each agent: verify StartEvent and StopEvent exist
5. For each process: verify WorkEvent/WorkRequestEvent pairs
6. Check for orphaned events (defined but never used in any @step)
7. Verify event serialization round-trips (Pydantic model_validate)

### 4.7 `debug-agent` — Agent debugging assistant

**Location**: `.claude/skills/debug-agent/SKILL.md`

```yaml
---
name: debug-agent
description: Debug an AI agent by tracing its event flow, checking NATS subscriptions,
  and analyzing Phoenix traces. Use when an agent isn't behaving as expected.
allowed-tools: Bash, Read, Grep, Glob
---
```

**Logic**:
1. Accept agent class name as argument
2. Find agent definition, read its @step methods
3. Map expected event flow (StartEvent → intermediate events → StopEvent)
4. Check if agent is registered (ClassDiscoveryRequest/Response)
5. Check NATS subscription status (via NATS monitoring: http://localhost:8222)
6. Check Phoenix traces for recent runs (via MCP or API)
7. Identify common issues: missing config, event type mismatch, step precondition failure

### 4.8 `release-prep` — Pre-release validation

**Location**: `.claude/skills/release-prep/SKILL.md`

```yaml
---
name: release-prep
description: Run comprehensive pre-release validation. Checks all scopes for
  formatting, linting, type checking, tests, documentation freshness, and
  version consistency. Use before merging to main.
allowed-tools: Bash, Read, Grep, Glob
---
```

**Logic**:
1. Run `make pr-ready` at root (all scopes: format + lint + typecheck)
2. Run `make test` in each scope with results tracking
3. Verify version consistency (all scopes at same aihub_lib tag)
4. Check for uncommitted changes
5. Verify PR title follows conventional commits
6. Check that changed scopes have updated documentation
7. Verify Docker compose generation is up to date (`make generate-compose`)
8. Report pass/fail for each check

---

## Phase 5: Custom Subagents (Week 4-5)

Specialized AI agents that run in isolated context windows for specific tasks.

### 5.1 `codebase-expert.md` — Deep knowledge builder

**Location**: `.claude/agents/codebase-expert.md`

```yaml
---
name: codebase-expert
description: Deep knowledge of the aihub-core monorepo. Understands how scopes
  interact, traces event flows, and explains architectural decisions. Use for
  understanding how features connect, finding relevant code, and answering
  architectural questions.
tools: Read, Grep, Glob
model: sonnet
memory: project
---
```

**Instructions**:
- Always start by reading the relevant scope's AGENTS.md
- Trace cross-scope connections (e.g., agent events → API WebSocket → frontend)
- Build persistent knowledge in MEMORY.md:
  - Key architectural patterns discovered
  - Important file locations by domain
  - Common code paths (auth flow, event flow, data flow)
  - Module relationship graph
  - Frequently referenced files

### 5.2 `code-reviewer.md` — Quality and security reviewer

**Location**: `.claude/agents/code-reviewer.md`

```yaml
---
name: code-reviewer
description: Reviews code for quality, security, and adherence to aihub-core
  standards. Checks against AGENTS.md conventions, OWASP vulnerabilities,
  type hints, and test coverage. Use when reviewing PRs or checking code quality.
tools: Read, Grep, Glob
model: sonnet
---
```

**Instructions**:
- Read the relevant scope's AGENTS.md for conventions
- Check coding style: type hints (mandatory), Pydantic over dicts, async consistently
- Security: OWASP top 10, no SQL injection in MongoDB queries, proper auth checks
- Architecture: Controller → Service → Entity separation, no cross-scope violations
- Testing: verify new code has corresponding tests, BDD for complex workflows
- Event system: proper ControlEvent vs DisplayEvent classification

### 5.3 `event-flow-analyzer.md` — Event system tracer

**Location**: `.claude/agents/event-flow-analyzer.md`

```yaml
---
name: event-flow-analyzer
description: Traces event flows through the Swiss AI Agent Protocol. Maps how
  events propagate from agents through NATS to the API and frontend. Use when
  debugging event routing or understanding data flow.
tools: Read, Grep, Glob
model: sonnet
memory: project
---
```

**Instructions**:
- Trace complete event lifecycle: Agent @step → NATS publish → API subscribe → WebSocket → Frontend
- Map ControlEvent flows (workflow execution) vs DisplayEvent flows (UI updates)
- Verify topic hierarchy (Thread → Display → Run scoping)
- Identify dead letters (published events with no subscribers)
- Build knowledge base of event routing patterns in MEMORY.md

### 5.4 `docker-ops.md` — Docker infrastructure expert

**Location**: `.claude/agents/docker-ops.md`

```yaml
---
name: docker-ops
description: Expert on the Docker infrastructure. Understands the 30+ services,
  their interconnections, health checks, and configuration. Use for Docker
  troubleshooting, service debugging, and infrastructure questions.
tools: Read, Grep, Glob, Bash
model: haiku
---
```

**Instructions**:
- Know the 5 network topology (proxy, backend, data, storage, egress)
- Understand service dependencies and startup order
- Know health check endpoints for each service
- Understand Jinja2 template-driven compose generation
- Can read compose-config.yml to determine image versions
- Familiar with all access points (ports, URLs)

### 5.5 `test-analyzer.md` — Test infrastructure expert

**Location**: `.claude/agents/test-analyzer.md`

```yaml
---
name: test-analyzer
description: Analyzes test coverage, identifies gaps, and suggests test
  improvements. Understands pytest-bdd, async testing, and the custom test
  runners (AgentTestRunner, ProcessTestRunner, ApiTestRunner, BotTestRunner).
tools: Read, Grep, Glob, Bash
model: sonnet
---
```

**Instructions**:
- Know the test runner hierarchy (AgentTestRunner, ProcessTestRunner, ApiTestRunner, BotTestRunner)
- Understand BDD patterns (Gherkin features, step implementations, @async_test)
- Identify untested code paths by comparing code vs test coverage
- Suggest test scenarios for new features
- Know test markers: @pytest.mark.slow, .azure, .flaky, .integration, .experimental
- Understand CI test execution (Docker services per scope, parallel matrix)

### 5.6 `frontend-analyzer.md` — Vue/Nuxt component expert

**Location**: `.claude/agents/frontend-analyzer.md`

```yaml
---
name: frontend-analyzer
description: Expert on the Nuxt 3 frontend. Understands composables, Pinia-Colada
  queries, PrimeVue components, VueFlow workflows, and the SDK generation pipeline.
  Use for frontend analysis and planning.
tools: Read, Grep, Glob
model: sonnet
---
```

**Instructions**:
- Know the composable pattern (defineQuery, defineMutation, useQueryCache)
- Understand SDK generation flow (API → OpenAPI → HeyAPI → TypeScript)
- Know PrimeVue component library and Tailwind conventions
- Understand i18n setup (4 locales, YAML files, useI18n)
- Know file-based routing conventions
- Trace data flow: SDK call → composable → component → PrimeVue

### 5.7 `documentation-keeper.md` — Docs freshness tracker

**Location**: `.claude/agents/documentation-keeper.md`

```yaml
---
name: documentation-keeper
description: Tracks documentation freshness against code changes. Identifies stale
  docs, missing READMEs, and outdated architecture descriptions. Use when
  documentation may be out of sync with code.
tools: Read, Grep, Glob
model: haiku
memory: project
---
```

**Instructions**:
- Compare git log dates of code files vs their documentation
- Check README.md files exist for all significant directories
- Verify AGENTS.md files reference current file paths (not stale)
- Check ADRs are current (decisions not superseded without documentation)
- Build MEMORY.md tracking known documentation gaps
- Verify VitePress docs match current architecture

---

## Phase 6: Enhanced MCP Integration (Week 5)

### 6.1 Phoenix MCP Server

**Location**: `.claude/mcp/mcp-phoenix.sh`

Already referenced in AGENTS.md at http://localhost:6006 but not configured.

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
# Phoenix exposes an MCP endpoint for AI observability
exec npx -y mcp-remote@latest http://localhost:6006/mcp
```

Register in `.mcp.json`:
```json
"phoenix": {
  "command": "./.claude/mcp/mcp-phoenix.sh"
}
```

**Enables**: Query traces, view LLM call details, analyze agent performance
directly from Claude Code sessions.

### 6.2 NATS Monitoring MCP Server

**Location**: `.claude/mcp/mcp-nats.sh`

NATS exposes monitoring at http://localhost:8222.

```bash
#!/bin/bash
set -e
# NATS monitoring API for message bus observability
exec npx -y mcp-remote@latest http://localhost:8222/mcp 2>/dev/null || \
  echo "NATS monitoring not available as MCP. Use HTTP: http://localhost:8222"
```

**Note**: NATS may not have a native MCP endpoint. In that case, create a
lightweight wrapper using `fastmcp` that exposes NATS monitoring endpoints
(`/connz`, `/routez`, `/subsz`, `/varz`) as MCP tools.

### 6.3 Review `.mcp.json` configuration

Update to include all configured servers with clear documentation:
```json
{
  "mcpServers": {
    "mongodb": {
      "command": "./.claude/mcp/mcp-mongodb.sh"
    },
    "aihub_api": {
      "command": "./.claude/mcp/mcp-aihub-api.sh"
    },
    "phoenix": {
      "command": "./.claude/mcp/mcp-phoenix.sh"
    }
  }
}
```

---

## Phase 7: Infrastructure & Quality Improvements (Week 5-6)

### 7.1 Root Makefile enhancements

Add missing targets to root Makefile:

```makefile
# Run all tests across all scopes (missing today!)
test:
	cd aihub_pipeline && poetry run pytest || echo "Pipeline: No tests"
	cd aihub_lib && poetry run pytest
	cd aihub_agent && poetry run pytest
	cd aihub_process && poetry run pytest
	cd aihub_api && poetry run pytest
	cd aihub_bot && poetry run pytest || echo "Bot: No tests"

# Show all available targets with descriptions
help:
	@echo "Available targets:"
	@echo "  make format      - Format all Python code (Ruff)"
	@echo "  make format-md   - Format all Markdown files"
	@echo "  make lint        - Lint all Python code (Ruff)"
	@echo "  make typecheck   - Type-check all scopes (MyPy)"
	@echo "  make pr-ready    - Format + lint (pre-commit gate)"
	@echo "  make test        - Run all tests across all scopes"
	@echo "  make up-dev      - Start Docker dev environment"
	@echo "  make generate-compose - Generate Docker Compose files"
	@echo "  make changelog   - Generate CHANGELOG.md"
	@echo "  make license-check - Check dependency licenses"
	@echo "  make use-local-core - Switch to local aihub_lib"
	@echo "  make use-remote-core TAG=vX.Y.Z - Switch to remote"
	@echo "  make local-cert  - Generate mkcert TLS certificates"
	@echo "  make clean       - Remove build artifacts"

# Clean build artifacts across all scopes
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name coverage.xml -delete 2>/dev/null || true
	find . -type f -name pytest.xml -delete 2>/dev/null || true
```

### 7.2 aihub_web Makefile enhancement

The web Makefile only has `pr-ready` (just `pnpm lint`). Add:

```makefile
format:
	cd aihub_web && pnpm lint --fix

lint:
	cd aihub_web && pnpm lint

test:
	@echo "No frontend tests configured. See aihub_web/AGENTS.md"

dev:
	cd aihub_web && pnpm dev

build:
	cd aihub_web && pnpm build

generate-sdk:
	cd aihub_web && pnpm generate-sdk
```

### 7.3 Pre-commit configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-yaml
      - id: check-toml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/executablebooks/mdformat
    rev: 0.7.17
    hooks:
      - id: mdformat
        additional_dependencies:
          - mdformat-gfm
          - mdformat-frontmatter
```

---

## Phase 8: Documentation & ADR (Week 6)

### 8.1 Create ADR

**File**: `aihub_doc/arc42/decisions/2026_02_11_claude-code-sota-enablement.md`

Document the entire migration:
- **Context**: Moving from legacy commands to modern Skills, adding hooks/agents/MCP
- **Decision Drivers**: Developer productivity, deterministic enforcement, context
  window efficiency, team standardization, onboarding speed
- **Decision**: Adopt Skills system (replacing commands), project-level hooks,
  custom subagents with memory, enhanced MCP, scaffolding workflows
- **Consequences**:
  - Positive: Faster onboarding, consistent code quality, reusable workflows,
    portable configuration
  - Negative: Initial migration effort, team needs to learn new invocations

### 8.2 Update root README.md

Update the "AI Coding Assistant Integration" section to reflect:
- Skills (not slash commands) — list all 15+ skills with descriptions
- Custom subagents — list all 7 with purposes
- Hooks — explain the 6 guardrails
- MCP servers — list all 3 with capabilities
- Quick start guide for new developers

### 8.3 Update root AGENTS.md

Add brief section on:
- `CLAUDE.local.md` pattern for personal overrides
- Skills invocation (`/skill-name`)
- Custom subagent usage
- Hook behavior (what gets auto-formatted, what gets blocked)

### 8.4 Create `.claude/README.md`

Document the `.claude/` directory structure for new contributors:
```markdown
# Claude Code Configuration

## Directory Structure
- `skills/` — Reusable workflow skills (invoked via /skill-name)
- `agents/` — Custom subagents with specialized roles
- `hooks/` — Deterministic automation scripts
- `mcp/` — Model Context Protocol server scripts
- `settings.json` — Hooks, permissions, and project config

## Quick Reference
- Run `/skills` to see all available skills
- Run `/agents` to see all custom subagents
- Run `/hooks` to see configured hooks
- Run `/mcp` to manage MCP servers
```

---

## Execution Summary

### File Count by Phase

| Phase | New Files | Modified Files | Deleted Files |
|-------|-----------|----------------|---------------|
| 1. Hooks & Settings | 8 | 2 | 0 |
| 2. Migrate Commands | 7 | 0 | 7 |
| 3. Scaffolding Skills | 6 | 0 | 0 |
| 4. DX Skills | 8 | 0 | 0 |
| 5. Subagents | 7 | 0 | 0 |
| 6. MCP | 2 | 1 | 0 |
| 7. Infrastructure | 1 | 3 | 0 |
| 8. Documentation | 4 | 2 | 0 |
| **Total** | **~43** | **~8** | **7** |

### Dependency Order

```
Phase 1 (Hooks) → Phase 2 (Skills Migration) → Phase 3 (Scaffolding Skills)
                                               → Phase 4 (DX Skills)
                                               → Phase 5 (Subagents)
Phase 1 → Phase 6 (MCP)
Phase 1 → Phase 7 (Infrastructure)
All phases → Phase 8 (Documentation)
```

Phase 1 is the foundation — everything else builds on having proper hooks and settings.
Phases 2-7 can be parallelized after Phase 1 completes.

### Verification Per Phase

After each phase:
1. Verify hooks fire correctly with test edits
2. Verify skills are listed via `/skills` and invocable via `/skill-name`
3. Verify subagents appear via `/agents`
4. Verify MCP servers connect via `/mcp`
5. Run `make pr-ready` in all modified scopes
6. Commit with conventional commit format: `feat(ci-cd): <description>`

# AI-Hub Developer Guide for AI Agents

## Project Overview

**Swiss AI-Hub**: Enterprise-grade, sovereign AI platform for integrating AI into business processes. A complete
production-ready ecosystem with batteries included (database, API, UI, pipelines, Docker deployment).

Tech Stack & Paradigms: Python 3 monorepo with Poetry. NATS pub-sub event-driven architecture. FastAPI REST APIs with
uvicorn + gunicorn. Custom OAuth2/OIDC auth (Azure AD). LlamaIndex workflow engine for transparent agents. Dagster
asset-based data pipelines. Nuxt 3 + Vue 3 frontend with TypeScript. PrimeVue UI components, FormKit forms, VueFlow
workflows. Docker Compose for all environments (dev, local, nightly, latest, GPU). VitePress docs with automated LLM
translation. Valkey (Redis v5 client) for state, FerretDB (MongoEngine) for persistence, Milvus for vectors. Azure SDK
suite (20+ packages). OpenTelemetry + OpenInference + Arize Phoenix for observability. Pydantic v2 validation. MyPy
strict type checking. pytest-bdd for Gherkin BDD tests. Black formatter, Ruff linter. pnpm for frontend. Pulumi for
Azure IaC.

**Core Philosophy**: Privacy-first, Swiss data sovereignty, security by design, radical transparency through
workflow-based agents (not black boxes).

**Three-Tier Architecture**:

- **Tier 1**: Secure LLM access via OpenWebUI chat interface
- **Tier 1+**: Integration with MS Teams, Slack, Outlook (Azure Bot Framework)
- **Tier 2**: AI agents with organizational knowledge (RAG, vector search)
- **Tier 3**: Process orchestration (agents + humans + external systems)

**Swiss AI Agent Protocol**: Internal event-driven protocol governing all communication between platform components.
Publish-subscribe model over NATS with strict Control Event (workflow) vs Display Event (observability) separation.
Hierarchical scoping (Thread → Display → Run) for security and tracing.

## Repository Structure

**Monorepo**: Single `aihub-core` repository containing all platform code. Open-source and reusable.

**Package Separation**: Code shared by 2+ services belongs in `aihub_lib`. Service-specific code stays in respective
packages.

## Package Architecture

**Monorepo Scopes** (Python packages):

**Foundation**:

- **`aihub_lib`**: Shared library used by all other packages. Place code here if used by 2+ services.

**Core Logic**:

- **`aihub_agent`**: Agent definitions and workflows (LlamaIndex-based, transparent, auditable).
- **`aihub_pipeline`**: Data ingestion/processing pipelines (Dagster).
- **`aihub_process`**: High-level business process orchestration (agents + humans + external programs).

**Integration**:

- **`aihub_api`**: REST API + WebSocket gateway (FastAPI).
- **`aihub_web`**: Frontend UI (Nuxt.js, Vue 3).
- **`aihub_bot`**: Collaboration platform integrations (MS Teams, Slack, etc.).

**Operations**:

- **`aihub_action`**: Reusable GitHub Actions for CI/CD.
- **`aihub_doc`**: arc42 documentation + ADRs.

## Key Terminology

- **AI Assistant**: Reactive, context-aware co-worker integrated with business data. User-initiated.
- **AI Agent**: Autonomous process partner that proactively executes tasks. Workflow-based, transparent, traceable.
- **Pipeline**: Dagster-based data ingestion/processing workflow.
- **Process**: Orchestrated collaboration between agents, humans, and programs.
- **Swiss AI Agent Protocol**: Internal event-driven communication protocol. NATS publish-subscribe with Control/Display
  event separation.

## Tech Stack

**Core Platform**:

- **OpenWebUI**: Primary chat interface with dual pipeline architecture (event-based for agents via SSE,
  OpenAI-compatible for direct model access)
- **LiteLLM**: Universal LLM gateway (unified interface for OpenAI, Anthropic, Google, local models). Cost tracking,
  request routing, retry policies.
- **Admin UI**: Nuxt.js-based management interface, developed by us

**AI/LLM**:

- **LlamaIndex**: Core framework for RAG
- **Providers**: OpenAI, Azure OpenAI, Google GenAI, Hugging Face, vLLM & llama.cpp (local models)

**Data/Storage**:

- **FerretDB**: MongoDB-compatible NoSQL (PostgreSQL backend), accessed via MongoEngine
- **Valkey**: Redis-compatible in-memory state storage for agents (RunContext, ThreadContext)
- **Milvus**: Primary vector store for semantic search
- **SeaweedFS**: S3-compatible object storage (files, artifacts)
- **PostgreSQL**: Relational database backend

**Backend**:

- **Python 3.13**: Core language
- **Poetry**: Dependency management
- **FastAPI**: REST API + WebSocket
- **Pydantic**: Data validation

**Observability**:

- **OpenTelemetry**: End-to-end distributed tracing
- **OpenInference**: LLM-specific instrumentation
- **Arize Phoenix**: AI observability and trace visualization (http://localhost:6006)

**Messaging**:

- **NATS**: Event-driven async communication backbone (Swiss AI Agent Protocol message bus)

**Deployment**:

- **Docker Compose**: Multi-environment support (dev, local, nightly, latest, GPU variants). 100% Docker Compose—no
  separate IaC tooling.
- **Traefik**: Reverse proxy and API gateway
- **OAuth2**: Enterprise authentication (Azure AD with superuser fallback for Docker deployments)

**Docker Compose Conventions**:

- **No default values in env var assignments**: Never use `${VAR:-default}` syntax in docker-compose templates. Define
  all default values in `.env.dev` and `.env.prod` files instead. This keeps defaults centralized and explicit.
- **Template location**: `deployment/templates/docker-compose.yml.j2` (Jinja2 template)
- **Config location**: `deployment/compose-config.yml` (image tags, stage-specific values)
- **Regenerate after changes**: Run `make generate-compose` after modifying templates or config

## Coding Style & Conventions

**Key Principles**:

01. **Type-hint everything**: Return types mandatory. Use `Annotated` for parameters. Modern syntax: `str | None` not
    `Optional[str]`, `list[str]` not `List[str]`.
02. **Pydantic over dicts/dataclasses**: Use Pydantic models for structured data (validation, serialization, SecretStr).
03. **Fail fast**: No defensive try-catch wrappers. Validate inputs immediately. Let exceptions propagate.
04. **Comments explain "why"**: Never "what" or "how" (code is self-documenting). Docstrings for design rationale.
05. **Async consistently**: All I/O operations (network, database, Redis) use async/await.
06. **Keep methods short**: < 50 lines, cognitive complexity < 15. Extract sub-functions if needed.
07. **Inheritance only when beneficial**: Event hierarchies, shared infrastructure, framework integration. Not for code
    reuse.
08. **No premature optimization**: Readability first. Optimize only when profiling shows bottlenecks.
09. **Descriptive naming**: `not_authorized_to_view_exception` not `auth_ex`. Classes: `CamelCase`, functions:
    `snake_case`, constants: `UPPER_SNAKE_CASE`.
10. **Modern Python**: Use `|` unions, `@property`, `@override`, `match/case`.
11. **Controller → Service → Entity**: Separation of concerns (HTTP layer → business logic → persistence).
12. **Dependency injection**: FastAPI `Depends` and `Security` for clean parameter injection.

**Example**:

```python
# Type-hint return, Annotated params, Pydantic, fail fast, async
async def api_key_for_user(
    user: Annotated[UserIdentity, Security(...)],
    client: Annotated[httpx.AsyncClient, Depends(...)],
) -> str:
    response = await client.get("/user/info", params={"user_id": user.id})
    response.raise_for_status()  # Fail fast
    return response.json()["key"]

class AgentDTO(BaseModel):  # Pydantic not dict
    agent_class: str
    is_online: bool
```

## Coding Conventions (Tools)

**Python** (Backend):

- **Formatter**: Black (line length: 120). Config: `/home/user/aihub-core/pyproject.toml`
- **Linter**: Ruff (rules: E, F, UP, I). Config: `/home/user/aihub-core/pyproject.toml`
- **Type Checker**: MyPy (`strict = true`). Config: `/home/user/aihub-core/pyproject.toml`
- **Naming**: `snake_case` for files/dirs, `CamelCase` for classes, `test_*.py` for tests
- **Types**: Mandatory type annotations. Use modern syntax (`list[int]`, `int | None`). Avoid complex types (dicts,
  tuples)—use Pydantic models or dataclasses
- **Error Handling**: Let functions fail. Do NOT catch errors and return None
- **Docstrings**: Required for all public modules/classes/methods. Explain "why", not "what". Never use `Args:` or
  `Returns:` sections—keep docstrings concise

## Development Workflow

### Setup

1. **Clone**: `git clone https://github.com/bbvch-ai/aihub-core`
2. **Python scopes**: `cd <scope>` → `poetry shell` → `poetry install`
3. **Frontend**: `cd aihub_web/aihub_web` → `pnpm install`
4. **Docker stack (dev)**: `docker compose -f docker-compose.dev.yml up -d`

### Pre-Commit Checklist (Per Scope)

Run from activated Poetry shell:

1. **`make pr-ready`**: Auto-format + lint + type check (MUST pass before commit)
2. **`make test`**: Run all tests (MUST pass before commit)

### Git Workflow

- **Branching**: `main` branch only. Feature branches: `<type>/short-description` (`feat/`, `fix/`, `chore/`, `test/`,
  `doc/`)
- **Commits**: Conventional Commits format: `<type>(<scope>): <subject>` (e.g., `feat(aihub): Add new agent workflow`)
- **PRs**: GitHub CLI (`gh pr create`). Squash merge only. Title must follow Conventional Commits
- **Protection**: `main` branch requires 1 approval, linear history, passing checks

### Task Completion Protocol

Before marking task complete:

1. **Code quality**: Run `make pr-ready` and `make test` in all modified scopes
2. **Documentation**:
   - Update docstrings for new/changed code
   - Update scope `README.md` if changes affect architecture/usage
   - Update root `/home/user/aihub-core/README.md` if changes affect overall platform
   - Create ADR in `/home/user/aihub-core/aihub_doc/arc42/decisions/` for significant architectural decisions
3. **Commit & push**: Follow Git workflow above

## Architectural Decisions (ADRs)

**CRITICAL**: Consult existing ADRs before significant changes. Located:
`/home/user/aihub-core/aihub_doc/arc42/decisions/`

**Create ADR if**:

- Adding major dependencies
- Introducing new tools/frameworks
- Altering fundamental patterns (e.g., Service/Controller/Repository abstraction, Swiss AI Agent Protocol)

**ADR Format**: `YYYY_MM_DD_short-decision-summary.md` (Context → Decision Drivers → Decision → Consequences)

## Work Management

**GitHub Project**:

- **Unified Project**: `gh project view 13 --owner bbvch-ai` (https://github.com/orgs/bbvch-ai/projects/13)
- Roadmap + backlog in one project, organized by monthly sprints

**Task Workflow**:

1. Find task: `gh issue list -R "bbvch-ai/aihub-core" -a "@me"`
2. View context: `gh issue view <issue_number> -c`
3. Track progress in project board

## Package Dependencies

**Inter-package refs**: All packages reference `aihub_lib` via Git URL in `pyproject.toml`. Versioning via Git tags.

**Local dev**: `make use-local-core` to switch to local `aihub_lib`.

**Dependency mgmt**: `poetry add/remove/update` (NEVER edit `pyproject.toml` or `poetry.lock` manually).

## Testing

**Framework**: pytest (Python), Vitest (frontend)

**Python**:

- **Location**: `tests/` dir at same level as code
- **Naming**: `test_*.py`
- **Markers**: `@pytest.mark.slow`, `@pytest.mark.integration` (defined in `pyproject.toml`)
- **BDD**: Use `pytest-bdd` for agent/process workflows (Gherkin `.feature` files in `tests/features/`)
- **Async**: pytest-bdd has limitations; use plain pytest for async tests
- **Run**: `make test` (within Poetry shell)

**Philosophy**: Pragmatic, not TDD. Write tests when straightforward. MUST run all tests before commit.

## Claude Code Integration

**Full documentation**: `/home/user/aihub-core/.claude/README.md`

**Skills** (30 total — invoke via `/skill-name`):

- **Documentation**: `/create-pr`, `/update-doc`, `/explain`, `/document-decision`, `/document-feature`,
  `/document-solution`, `/implement-feedback-from-pr`
- **Scaffolding**: `/scaffold-agent`, `/scaffold-pipeline`, `/scaffold-process`, `/scaffold-api-endpoint`,
  `/scaffold-frontend-page`, `/scaffold-bot-handler`
- **Developer Experience**: `/test-scope`, `/docker-dev`, `/check-i18n`, `/generate-sdk`, `/dependency-audit`,
  `/validate-events`, `/debug-agent`, `/release-prep`
- **Frontend**: `/scaffold-composable`, `/scaffold-event-display`, `/scaffold-dashboard-widget`,
  `/debug-frontend`, `/audit-frontend`, `/primevue-lookup`, `/scaffold-frontend-subpage`,
  `/scaffold-frontend-component`, `/design-system`

**Custom Subagents** (7 — Claude Code uses these automatically for specialized tasks):

- `codebase-expert` (with memory), `code-reviewer`, `event-flow-analyzer` (with memory), `docker-ops`,
  `test-analyzer`, `frontend-analyzer`, `documentation-keeper` (with memory)

**Hooks** (6 — run automatically, no invocation needed):

- `auto-format-python.sh` (PostToolUse): Ruff format + check on Python file edits
- `auto-format-frontend.sh` (PostToolUse): ESLint fix on TS/Vue file edits
- `protect-sensitive-files.sh` (PreToolUse): Blocks access to .env, .pem, .key, credentials
- `scope-boundary-check.sh` (PreToolUse): Warns about cross-scope import violations
- `stop-hook-git-check.sh` (Stop): Checks uncommitted changes at session end
- `session-start.sh` (SessionStart): Installs dependencies, checks environment

**Local overrides** (gitignored): `CLAUDE.local.md`, `.claude/settings.local.json`, `.claude/mcp.local.json`

## MCP Integration (AI Assistant Context)

**Model Context Protocol**: Provides AI assistants (Claude Code, Gemini CLI) with development environment access.

**Config**: `/home/user/aihub-core/.mcp.json`

**MCP Servers** (12 total, 11 enabled by default):

Platform servers (require running Docker dev stack):

- **Phoenix MCP**: AI observability/tracing data (http://localhost:6006)
- **MongoDB MCP**: Read-only database access (FerretDB/MongoDB layer)
- **AI-Hub API MCP**: API endpoint testing (http://localhost:8000/mcp)
- **PostgreSQL MCP**: Read-only access to infrastructure databases (Phoenix, Dagster, LiteLLM, OpenWebUI)
- **Milvus MCP**: Vector database operations — manage collections, run similarity searches, inspect indexes
- **NATS MCP**: Messaging system — inspect subjects, view messages, monitor JetStream streams
- **Dagster MCP**: Pipeline orchestration — explore pipelines, monitor runs, manage assets

Development servers (work independently):

- **Context7 MCP**: Up-to-date library documentation for LlamaIndex, FastAPI, Pydantic, and other dependencies
- **PrimeVue MCP**: Official component library docs — props, events, slots, theming, Pass Through, design tokens
- **Nuxt MCP**: Official framework docs, API references, deployment guides (remote at nuxt.com/mcp)
- **Playwright MCP**: Browser automation and UI debugging for the Nuxt 3 admin interface (headless Chromium)
- **GitHub MCP**: Issues, PRs, code search, CI status (disabled — requires `GITHUB_PERSONAL_ACCESS_TOKEN` in `.env`)

## Quick Reference

**Essential Files**:

- Root README (human-friendly): `/home/user/aihub-core/README.md`
- Docker Compose (dev): `/home/user/aihub-core/docker-compose.dev.yml`
- Env config: `/home/user/aihub-core/.env` (copy from `.env.dev`)
- Makefile (per scope): `/home/user/aihub-core/<scope>/Makefile`
- ADRs: `/home/user/aihub-core/aihub_doc/arc42/decisions/`
- Architecture docs: `/home/user/aihub-core/aihub_doc/docs/2_platform/2_architecture/`
- Swiss AI Agent Protocol:
  `/home/user/aihub-core/aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/index.en.md`

**Common Commands** (within scope dir, Poetry shell activated):

- `poetry install`: Install dependencies
- `poetry add <pkg>`: Add dependency
- `make format`: Run Black formatter
- `make lint`: Run Ruff + MyPy
- `make pr-ready`: Format + lint with auto-fix (RUN BEFORE COMMIT)
- `make test`: Run pytest suite (RUN BEFORE COMMIT)

**Access Points** (docker-compose.dev.yml):

- OpenWebUI: http://localhost:8080
- Admin UI: http://localhost:3000
- API: http://localhost:8000
- Dagster: http://localhost:3000
- Phoenix: http://localhost:6006
- SeaweedFS: http://localhost:8889

## Scope-Specific Guidance

Each package has its own `AGENTS.md` with scope-specific architecture, folder structure, and examples. Consult before
working on a scope:

- `/home/user/aihub-core/aihub_lib/AGENTS.md`
- `/home/user/aihub-core/aihub_agent/AGENTS.md`
- `/home/user/aihub-core/aihub_api/AGENTS.md`
- `/home/user/aihub-core/aihub_bot/AGENTS.md`
- `/home/user/aihub-core/aihub_pipeline/AGENTS.md`
- `/home/user/aihub-core/aihub_process/AGENTS.md`
- `/home/user/aihub-core/aihub_web/AGENTS.md`
- `/home/user/aihub-core/aihub_action/AGENTS.md`
- `/home/user/aihub-core/aihub_doc/AGENTS.md`

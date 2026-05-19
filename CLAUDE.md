# Swiss AI Hub Developer Guide for AI Agents

## Project Overview

**Swiss AI Hub**: Open-source, self-hosted AI platform for enterprises. Organizations run it on their own infrastructure
— no SaaS dependency, full data sovereignty. The platform handles authentication, multi-tenancy, cost control,
observability, LLM routing, vector storage, and document parsing as commodity infrastructure. Developers focus on
building agents, pipelines, and processes using the SDK; the platform provides the runtime.

**Platform vs SDK**: The platform is the runtime infrastructure (Docker, Traefik, LiteLLM, Milvus, Dagster, NATS,
PostgreSQL — handles SSO, routing, cost tracking, UI hosting). The SDK is where you build: agents, data pipelines, bot
integrations, and processes. SDK code inherits all platform capabilities — no custom REST APIs, WebSocket management,
database schemas, or auth logic needed.

**Swiss AI Agent Protocol**: Event-driven protocol over NATS. Strict Control Event (workflow) vs Display Event
(observability) separation. Hierarchical scoping (Thread → Display → Run). See
`docs/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/index.en.md`.

## Platform Architecture

The platform follows an event-driven microservice architecture where NATS serves as the central communication backbone.
All inter-component communication flows through the Swiss AI Agent Protocol, which distinguishes between Control Events
(workflow state transitions consumed by agents and orchestrators) and Display Events (observability data consumed by
frontends and tracing systems). This separation allows the chat UI to visualize agent reasoning in real-time without
interfering with workflow execution.

**LLM Gateway**: All model access is mediated by LiteLLM, which provides a unified OpenAI-compatible interface to cloud
providers (Swiss LLM Cloud), local models (vLLM for chat, embedding, and reranking on GPU deployments), and audio models
(Speaches for STT/TTS). Presidio intercepts requests for PII detection and anonymization before they reach external
providers. This gateway pattern decouples application code from specific providers — switching models requires only a
configuration change in LiteLLM, not code modifications.

**Agent Runtime**: Agents run as independent microservices that subscribe to NATS topics and publish events. The
dispatcher replays the event history from JetStream to determine which steps to execute, while durable state in Valkey
(RunContext, ThreadContext) holds arbitrary agent-set data that cannot be reconstructed from events. Agents access
organizational knowledge through Milvus vector search, where document embeddings are indexed for semantic retrieval.
This design allows agents to scale horizontally and be deployed or updated independently without affecting the rest of
the platform.

**Data Pipeline**: Dagster orchestrates the ingestion workflow: sources (SharePoint, OneDrive via Rclone) are monitored
for changes, documents are downloaded to SeaweedFS, parsed by MinerU (OCR + structural extraction), chunked
semantically, embedded via configured models, and stored in Milvus. The asset-based pipeline model provides lineage from
every vector embedding back to its source document.

**Process Orchestration**: The process engine coordinates multi-step workflows involving agents, humans, and external
systems (Power Automate, n8n, UiPath). Process state is persisted in FerretDB (MongoDB-compatible API over PostgreSQL).
When a step requires human judgment, a task appears in the Process UI; when it requires AI, the engine delegates to an
agent via NATS; when it requires an external action, it triggers a webhook.

**Storage Layer**: The platform uses purpose-specific storage: PostgreSQL for relational data (OpenWebUI, Langfuse,
Dagster, LiteLLM), FerretDB for document storage (conversations, app data, events), Milvus for vector embeddings,
SeaweedFS for S3-compatible file storage (uploads, artifacts, pipeline data), Valkey for ephemeral agent state, and
Neo4j for graph-based memory. etcd serves as the metadata backend for both Milvus and SeaweedFS.

**Observability**: OpenTelemetry collects distributed traces across all services, forwarded by the OTEL Collector.
Langfuse adds AI-specific observability on top — full prompt/response capture, per-trace cost tracking, RAG retrieval
tracing, and evaluation datasets. Both integrate via the same trace context, providing end-to-end visibility from user
request to LLM response.

**Network Isolation**: Docker Compose defines five network zones: `proxy` (external ingress via Traefik), `backend`
(application services), `data` (databases, caches, message broker), `storage` (SeaweedFS cluster), and `egress`
(outbound internet with inter-container communication disabled). Services are assigned only the networks they require.

## Dev Stack Services

The `infra/docker-compose.dev.yml` runs ~30 containers. Key services by role:

**User-Facing**: OpenWebUI (chat UI, :8080), Admin UI and Process UI (Nuxt, :3333, run locally outside Docker)

**API & Gateway**: FastAPI REST + WebSocket (:8000, run locally), LiteLLM universal LLM proxy (:4000), Traefik reverse
proxy (production only)

**AI Inference**: Speaches STT/TTS (:8185), Presidio analyzer + anonymizer (PII filtering). GPU deployments add vLLM for
local chat, embedding, and reranking. Non-GPU deployments route all inference to Swiss LLM Cloud.

**Databases**: PostgreSQL with pgvector (:5432, 4 DBs: openwebui/langfuse/dagster/litellm), FerretDB (:27017,
MongoDB-compatible over its own PostgreSQL), Milvus vector DB (:19530), Neo4j graph DB (:7474/:7687), Valkey/Redis
(:6379), ClickHouse (Langfuse analytics), etcd (metadata for Milvus + SeaweedFS)

**Storage**: SeaweedFS cluster (master + volume + filer + S3 gateway at :9000, filer UI at :8889), Rclone cloud sync
(:5572)

**Pipelines**: Dagster orchestrator (:3000, run locally), pipeline workers (run locally)

**Document Processing**: MinerU OCR + parsing (:5001)

**Backup**: Backup Dagster webserver (:3004), gRPC code server, daemon — independent Dagster instance for scheduled
backup/restore

**Observability**: Langfuse web (:6006) + worker, OTEL Collector (:4317/:4318)

**Utility**: Jupyter Lab (:8888, code execution sandbox), Playwright (:3036, browser automation), Attu (:3003, Milvus
admin UI)

## Package Architecture

Code shared by 2+ services belongs in `packages/core`. Service-specific code stays in its scope.

- **`packages/core`**: Shared library (Swiss AI Hub Core) used by all other packages.
- **`packages/agent`**: Agent definitions and workflows (Our custom Workflow-Engine, transparent, auditable).
- **`packages/pipeline`**: Data ingestion/processing pipelines (Dagster).
- **`packages/process`**: High-level business process orchestration (agents + humans + external programs).
- **`packages/api`**: REST API + WebSocket gateway (FastAPI).
- **`packages/web`**: Frontend UI (Nuxt 3, Vue 3, PrimeVue, Tailwind).
- **`packages/bot`**: Collaboration platform integrations (MS Teams, Slack).
- **`packages/backup`**: Centralized backup/restore service (independent Dagster instance).
- **`.github/actions`**: Reusable GitHub Actions for CI/CD.
- **`docs`**: arc42 documentation + ADRs (VitePress).

Each scope has its own `CLAUDE.md` — consult it before working in that scope.

## Key Terminology

- **AI Assistant**: Reactive, context-aware co-worker integrated with business data. User-initiated.
- **AI Agent**: Autonomous process partner that proactively executes tasks. Workflow-based, transparent, traceable.
- **Pipeline**: Dagster-based data ingestion/processing workflow.
- **Process**: Orchestrated collaboration between agents, humans, and programs.

## Coding Conventions

01. **Type-hint everything**: Return types mandatory. Use `Annotated` for parameters. Modern syntax: `str | None` not
    `Optional[str]`, `list[str]` not `List[str]`.
02. **Pydantic over dicts/dataclasses**: Always Pydantic models, never dataclasses. Add `@classmethod` factory methods
    like `from_entity()`, `from_request()` to make construction easier.
03. **Fail fast**: No defensive try-catch wrappers. No catching errors to return None. Let exceptions propagate.
04. **No comments**: Never comment what code does — code is self-documenting. Only explain "why" when non-obvious.
05. **Async consistently**: All I/O operations (network, database, Redis) use async/await.
06. **Keep methods short**: < 50 lines, cognitive complexity < 15. Extract sub-functions if needed.
07. **Inheritance only when beneficial**: Event hierarchies, shared infrastructure, framework integration. Not for code
    reuse.
08. **No premature optimization**: Readability first. Optimize only when profiling shows bottlenecks.
09. **Descriptive naming**: `not_authorized_to_view_exception` not `auth_ex`. Classes: `CamelCase`, functions:
    `snake_case`, constants: `UPPER_SNAKE_CASE`.
10. **Modern Python**: Use `|` unions, `@property`, `@override`, `match/case`. Return `Self` (from `typing`) instead of
    `"ClassName"` for methods returning own type. Use PEP 695 generic syntax `class Foo[T: Bound]:` and
    `def bar[T](x: T)` instead of `TypeVar`. See `packages/core/swiss_ai_hub/core/subscribers/abstract_subscriber.py`
    for the pattern.
11. **Controller → Service → Entity**: Separation of concerns (HTTP layer → business logic → persistence).
12. **Dependency injection**: FastAPI `Depends` and `Security` for clean parameter injection.
13. **One class per file**: Each file should contain a single primary class. File names are always `snake_case`
    (`my_class.py`), class names are always `CamelCase` (`MyClass`).
14. **No loose functions**: Avoid files containing standalone functions. Create service classes with `@staticmethod` or
    `@classmethod` methods instead.
15. **No backwards compatibility**: Breaking changes are fine. Do not add compatibility shims, re-exports, or renamed
    aliases unless explicitly asked.
16. **No new abstractions**: Do not introduce abstractions that do not follow existing patterns in the codebase.
17. **`__init__.py` exports**: Each top-level folder within a package should have an `__init__.py` that lazily exports
    the public interface (using `TYPE_CHECKING` + `__getattr__`). Deeper nested folders rarely need `__init__.py`.
18. **Import rules — within a package**: Always import via the full module path to the source file, never through
    `__init__.py` re-exports. E.g., `from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent`.
19. **Import rules — across packages**: Always import through the target package's public interface (`__init__.py`),
    never access internal modules directly. E.g., `from swiss_ai_hub.core.events.agent import StartEvent`.
20. **Environment variables**: Pydantic `BaseSettings` classes do NOT auto-load from environment variables. Environment
    variables must be loaded explicitly when constructing settings instances.

**Naming**: `snake_case` for files/dirs, `CamelCase` for classes, `test_*.py` for tests.

**Docstrings**: Explain "why", not "what". Never use `Args:` or `Returns:` sections — use type hints and `Annotated`
instead. Keep docstrings concise, one or two sentences max.

## Tooling

**What hooks handle automatically — do NOT run these manually:**

- **Formatting** (PostToolUse hooks on every file edit): Ruff format for Python, ESLint --fix for TS/Vue, mdformat for
  Markdown, yamlfix for YAML. Config: per-scope `pyproject.toml`, `packages/web/eslint.config.js`.
- **Linting** (PostToolUse hook): Ruff check --fix (rules: E pycodestyle, F pyflakes, UP pyupgrade, I isort).
- **`make pr-ready`** (stop hook at session end): Automatically runs on all dirty scopes before session closes.
  Hard-blocks if it fails. Do not run manually mid-session — it runs at the end.
- **`uv.lock` protection** (PreToolUse hook): Edits to `uv.lock` are hard-blocked. Use `uv add/remove`.
- **Scope boundary checks** (PreToolUse hook): Warns if you import directly between scopes instead of through
  `packages/core`.
- **Dependency setup** (SessionStart hook): `uv sync --all-packages` + `pnpm install` run at session start.

**What you MUST run manually:**

- **`make test`**: Run pytest in all modified scopes. No hook automates this.

## Commands

Run from the workspace root:

| Command        | What it does                                        |
| -------------- | --------------------------------------------------- |
| `make test`    | Run pytest suite (MUST pass before commit)          |
| `uv add <pkg>` | Add dependency (NEVER edit pyproject.toml manually) |
| `uv sync`      | Sync all packages from lockfile                     |

## Development Workflow

### Git Workflow

**Branch naming** (CI-enforced via `branchlint`):

- Feature branches: `^([a-z]{2,})\/([a-z-0-9]{2,})$` — e.g., `feat/add-auth`, `fix/login-bug`
- Claude branches: `^claude\/[a-zA-Z0-9-]+$` — e.g., `claude/fix-issue-42`
- No uppercase, no underscores in branch names. Prefix must be all-lowercase (`feat`, `fix`, `chore`, `test`, `doc`).

**Commits**: Conventional Commits: `<type>(<scope>): <subject>` (e.g., `feat(swiss-ai-hub): Add new agent workflow`)

**PR title** (CI-enforced via `semantic-pr`):

- Format: `<type>(<scope>): <Subject starting with uppercase>`
- Scope is **mandatory**.
- Allowed types: `fix`, `feat`, `doc`, `test`, `chore`
- Allowed scopes: `swiss-ai-hub`, `iac`, `ci-cd`, `bots`, `dagster`, `deploy`, `ui`, `guards`, `rag`, `tracing`,
  `workflows`, `backup`

**PR labels** (CI-enforced): Every PR must have exactly one version label: `major`, `minor`, or `patch`. Controls
automatic semver bumps on merge.

**Merge**: Squash merge only. `main` requires 1 approval, linear history, passing checks. Draft PRs skip CI (except
frontend lint).

### Task Completion Protocol

Before marking task complete (`make pr-ready` runs automatically via stop hook):

1. Run `make test` in all modified scopes (not automated by any hook)
2. Update docstrings for new/changed code
3. Update scope `README.md` if changes affect architecture/usage
4. Create ADR in `docs/arc42/decisions/` for significant architectural decisions
5. Commit & push following Git workflow above

## Testing

**Framework**: pytest (Python), Vitest (frontend — not yet configured)

- **Location**: `tests/` dir at same level as code
- **Naming**: `test_*.py`
- **Markers**: `slow`, `integration`, `flaky`, `self_hosted`, `experimental` (per-scope `pyproject.toml`)
- **CI excludes**: `pytest -m "not flaky"` — flaky tests skip in CI
- **BDD**: Use `pytest-bdd` for agent/process workflows (Gherkin `.feature` files in `tests/features/`)
- **Async**: pytest-bdd has limitations; use plain pytest for async tests

**Philosophy**: Pragmatic, not TDD. Write tests when straightforward. MUST run all tests before commit.

## Architectural Decisions (ADRs)

**CRITICAL**: Consult existing ADRs before significant changes. Located: `docs/arc42/decisions/`

**Create ADR if**: Adding major dependencies, introducing new tools/frameworks, or altering fundamental patterns.

**ADR Format**: `YYYY_MM_DD_short-decision-summary.md` (Context → Decision Drivers → Decision → Consequences)

## Package Dependencies

- All packages reference `packages/core` as a workspace dependency via `[tool.uv.sources]`.
- Use `uv add/remove` — NEVER edit `pyproject.toml` manually.

## Docker Compose Conventions

- **No default values in env var assignments**: Never use `${VAR:-default}` syntax in docker-compose templates. Define
  all default values in `.env.dev` and `.env.prod` files instead.
- **Template**: `infra/deployment/templates/docker-compose.yml.j2` (Jinja2)
- **Config**: `infra/deployment/compose-config.yml` (image tags, stage-specific values)
- **Regenerate**: Run `make generate-compose` after modifying templates or config

## MCP & Claude Code

Skills, hooks, agents, and MCP servers are configured in `.claude/`. Claude Code discovers these automatically — see
`.claude/README.md` for full documentation.

Platform MCP servers (MongoDB, PostgreSQL, NATS, Milvus, Dagster, Langfuse, API) require the Docker dev stack running.
Development MCP servers (Context7, PrimeVue, Nuxt, Playwright) work independently.

Local overrides (gitignored): `CLAUDE.local.md`, `.claude/settings.local.json`, `.claude/mcp.local.json`

## Quick Reference

**Access Points** (infra/docker-compose.dev.yml):

| Service   | URL                   |
| --------- | --------------------- |
| OpenWebUI | http://localhost:8080 |
| Admin UI  | http://localhost:3333 |
| API       | http://localhost:8000 |
| Dagster   | http://localhost:3000 |
| Backup UI | http://localhost:3004 |
| Langfuse  | http://localhost:6006 |
| SeaweedFS | http://localhost:8889 |

**Key Paths**:

- ADRs: `docs/arc42/decisions/`
- Architecture docs: `docs/docs/2_platform/2_architecture/`
- Docker Compose (dev): `infra/docker-compose.dev.yml`
- Env config: `.env` (copy from `.env.dev`)

**Work Management**: `gh issue list -R "bbvch-ai/aihub-core" -a "@me"` | `gh project view 13 --owner bbvch-ai`

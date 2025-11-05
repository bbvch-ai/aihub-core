# AI-Hub Developer Guide for AI Agents

## Project Overview

**Swiss AI-Hub**: Enterprise-grade, sovereign AI platform for integrating AI into business processes. Not a library—a complete production-ready ecosystem with batteries included (database, API, UI, pipelines, Docker deployment).

**Core Philosophy**: Privacy-first, Swiss data sovereignty, security by design, radical transparency through workflow-based agents (not black boxes).

## Repository Structure

**Monorepo**: Two repository types:
- **`aihub-core`** (THIS REPO): Shared, reusable platform code. NEVER contains customer-specific information.
- **`aihub-<CUSTOMER>`**: Customer-specific implementations that extend `aihub-core`.

**Critical**: Changes here affect ALL customer projects. Maintain strict separation of concerns.

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
- **`aihub_web`**: Frontend UI (Nuxt.js, Vue 3, TypeScript).
- **`aihub_bot`**: Collaboration platform integrations (MS Teams, etc.).

**Operations**:
- **`aihub_action`**: Reusable GitHub Actions for CI/CD.
- **`aihub_iac`**: Infrastructure-as-Code (Terraform, cloud resources).
- **`aihub_doc`**: arc42 documentation + ADRs.

## Key Terminology

- **AI Assistant**: Reactive, context-aware co-worker integrated with business data. User-initiated.
- **AI Agent**: Autonomous process partner that proactively executes tasks. Workflow-based, transparent, traceable.
- **Pipeline**: Dagster-based data ingestion/processing workflow.
- **Process**: Orchestrated collaboration between agents, humans, and programs.

## Tech Stack

**AI/LLM**: LlamaIndex (core framework), OpenAI, Azure OpenAI, Google GenAI, Hugging Face.

**Data/Storage**:
- **FerretDB**: MongoDB-compatible NoSQL (PostgreSQL backend), accessed via MongoEngine.
- **Valkey**: Redis-compatible in-memory cache.
- **Vector Stores**: Azure AI Search (primary), Milvus (alternative).
- **File Storage**: SeaweedFS (S3-compatible), Azure Data Lake Storage.

**Backend**: Python 3.13, Poetry (dependency management), FastAPI, Pydantic.

**Frontend**: Nuxt.js (3.x), Vue 3 Composition API, TypeScript, pnpm.

**Observability**: OpenTelemetry, OpenInference, Arize Phoenix (LLM tracing).

**Messaging**: NATS (async communication).

**Deployment**: Docker Compose, Traefik (reverse proxy), multi-environment support.

## Coding Conventions

**Python** (Backend):
- **Formatter**: Black (line length: 120). Config: `/home/user/aihub-core/pyproject.toml`
- **Linter**: Ruff (rules: E, F, UP, I). Config: `/home/user/aihub-core/pyproject.toml`
- **Type Checker**: MyPy (`strict = true`). Config: `/home/user/aihub-core/pyproject.toml`
- **Naming**: `snake_case` for files/dirs, `CamelCase` for classes, `test_*.py` for tests.
- **Types**: Mandatory type annotations. Use modern syntax (`list[int]`, `int | None`). Avoid complex types (dicts, tuples)—use Pydantic models or dataclasses.
- **Error Handling**: Let functions fail. Do NOT catch errors and return None.
- **Docstrings**: Required for all public modules/classes/methods. Explain "why", not "what".

**TypeScript** (Frontend):
- **Linter**: ESLint (SonarJS recommended rules). Config: `/home/user/aihub-core/aihub_web/.eslintrc.cjs`
- **Formatter**: Prettier. Config: `/home/user/aihub-core/aihub_web/.prettierrc`
- **Style**: Vue 3 Composition API, TypeScript strict mode, composables for reusable logic.
- **Naming**: `camelCase` for variables/functions, `PascalCase` for components/types.

## Development Workflow

### Setup
1. **Clone**: `git clone https://github.com/bbvch-ai/aihub-core`
2. **Python scopes**: `cd <scope>` → `poetry shell` → `poetry install`
3. **Frontend**: `cd aihub_web` → `pnpm install`
4. **Docker stack**: `docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d`
5. **Local dev with SSL**: `make local-cert` → `docker compose -f docker-compose.local.yml up -d` (Access: https://127.0.0.1.nip.io)

### Pre-Commit Checklist (Per Scope)
Run from activated Poetry shell:
1. **`make pr-ready`**: Auto-format + lint + type check (MUST pass before commit).
2. **`make test`**: Run all tests (MUST pass before commit).

### Git Workflow
- **Branching**: `main` branch only. Feature branches: `<type>/short-description` (`feat/`, `fix/`, `chore/`, `test/`, `doc/`).
- **Commits**: Conventional Commits format: `<type>(<scope>): <subject>` (e.g., `feat(aihub): Add new agent workflow`).
- **PRs**: GitHub CLI (`gh pr create`). Squash merge only. Title must follow Conventional Commits.
- **Protection**: `main` branch requires 1 approval, linear history, passing checks.

### Task Completion Protocol
Before marking task complete:
1. **Code quality**: Run `make pr-ready` and `make test` in all modified scopes.
2. **Documentation**:
   - Update docstrings for new/changed code.
   - Update scope `README.md` if changes affect architecture/usage.
   - Update root `/home/user/aihub-core/README.md` if changes affect overall platform.
   - Create ADR in `/home/user/aihub-core/aihub_doc/arc42/decisions/` for significant architectural decisions.
3. **Commit & push**: Follow Git workflow above.

## Architectural Decisions (ADRs)

**CRITICAL**: Consult existing ADRs before significant changes. Located: `/home/user/aihub-core/aihub_doc/arc42/decisions/`

**Create ADR if**:
- Adding major dependencies
- Introducing new tools/frameworks
- Altering fundamental patterns (e.g., Service/Controller/Repository abstraction)

**ADR Format**: `YYYY_MM_DD_short-decision-summary.md` (Context → Decision Drivers → Decision → Consequences).

## Work Management

**GitHub Projects**:
- **Roadmap**: `gh project view 7 --owner bbvch-ai` (https://github.com/orgs/bbvch-ai/projects/7)
- **Kanban**: `gh project view 2 --owner bbvch-ai` (https://github.com/orgs/bbvch-ai/projects/2)

**Task Workflow**:
1. Find task: `gh issue list -R "bbvch-ai/aihub-core" -a "@me"`
2. View context: `gh issue view <issue_number> -c`
3. Link to roadmap: Check issue title prefix (e.g., `[process]`) → `gh issue view <parent_issue> -c`
4. Move to "In Progress" on Kanban when starting.
5. Move to "Done" when complete.

## Package Dependencies

**Inter-package refs**: All packages reference `aihub_lib` via Git URL in `pyproject.toml`. Versioning via Git tags.

**Local dev**: `make use-local-core` to switch to local `aihub_lib`.

**Dependency mgmt**: `poetry add/remove/update` (NEVER edit `pyproject.toml` or `poetry.lock` manually).

## Testing

**Framework**: pytest (Python), Vitest (frontend).

**Python**:
- **Location**: `tests/` dir at same level as code.
- **Naming**: `test_*.py`
- **Markers**: `@pytest.mark.azure`, `@pytest.mark.slow`, `@pytest.mark.integration` (defined in `pyproject.toml`).
- **BDD**: Use `pytest-bdd` for agent/process workflows (Gherkin `.feature` files in `tests/features/`).
- **Async**: pytest-bdd has limitations; use plain pytest for async tests.
- **Run**: `make test` (within Poetry shell).

**Philosophy**: Pragmatic, not TDD. Write tests when straightforward. MUST run all tests before commit.

## MCP Integration (AI Assistant Context)

**Model Context Protocol**: Provides AI assistants (Claude Code, Gemini CLI) with development environment access.

**Config**: `/home/user/aihub-core/.mcp.json`

**MCP Servers**:
- **Phoenix MCP**: AI observability/tracing data (http://localhost:6006).
- **MongoDB MCP**: Read-only database access (mongodb://admin:admin@localhost:27017/aihub).
- **AI-Hub API MCP**: API endpoint testing (http://localhost:8000/mcp).

## Quick Reference

**Essential Files**:
- Root README (human-friendly): `/home/user/aihub-core/README.md`
- Docker Compose: `/home/user/aihub-core/docker-compose.yml`
- Env config: `/home/user/aihub-core/.env` (copy from `.env.dev`)
- Makefile (per scope): `/home/user/aihub-core/<scope>/Makefile`
- ADRs: `/home/user/aihub-core/aihub_doc/arc42/decisions/`

**Common Commands** (within scope dir, Poetry shell activated):
- `poetry install`: Install dependencies
- `poetry add <pkg>`: Add dependency
- `make format`: Run Black formatter
- `make lint`: Run Ruff + MyPy
- `make pr-ready`: Format + lint with auto-fix (RUN BEFORE COMMIT)
- `make test`: Run pytest suite (RUN BEFORE COMMIT)

**Access Points** (docker-compose.local.yml):
- Web UI: https://127.0.0.1.nip.io
- API: https://127.0.0.1.nip.io/api
- OpenWebUI: https://openwebui.127.0.0.1.nip.io
- Dagster: https://dagster.127.0.0.1.nip.io
- Phoenix: http://localhost:6006

## Scope-Specific Guidance

Each package has its own `AGENTS.md` with scope-specific architecture, folder structure, and examples. Consult before working on a scope:
- `/home/user/aihub-core/aihub_lib/AGENTS.md`
- `/home/user/aihub-core/aihub_agent/AGENTS.md`
- `/home/user/aihub-core/aihub_api/AGENTS.md`
- `/home/user/aihub-core/aihub_bot/AGENTS.md`
- `/home/user/aihub-core/aihub_pipeline/AGENTS.md`
- `/home/user/aihub-core/aihub_process/AGENTS.md`
- `/home/user/aihub-core/aihub_web/AGENTS.md`
- `/home/user/aihub-core/aihub_action/AGENTS.md`
- `/home/user/aihub-core/aihub_iac/AGENTS.md`
- `/home/user/aihub-core/aihub_doc/AGENTS.md`

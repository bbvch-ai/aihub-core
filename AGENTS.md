# AI-Hub Developer Guide for AI Agents

## Project Overview

**Swiss AI-Hub**: Enterprise-grade, sovereign AI platform for integrating AI into business processes. Not a library—a complete production-ready ecosystem with batteries included (database, API, UI, pipelines, Docker deployment).

**Tech Stack & Paradigms**: **Python 3.13** monorepo with **Poetry 2.1.1**. **NATS** pub-sub event-driven architecture. **FastAPI 0.115** REST APIs with **uvicorn + gunicorn**. Custom OAuth2/OIDC auth (Azure AD). **LlamaIndex 0.12.33+** workflow engine for transparent agents. **Dagster 1.11** asset-based data pipelines. **Nuxt 3.17** + **Vue 3.5** frontend with **TypeScript**. **PrimeVue 4.3** UI components, **FormKit** forms, **VueFlow** workflows. **Docker Compose** for all environments (dev, local, nightly, latest, GPU). **VitePress 2.0-alpha** docs with automated LLM translation. **Valkey** (Redis 5.2 client) for state, **FerretDB** (MongoEngine) for persistence, **Milvus** for vectors. **Azure SDK** suite (20+ packages). **OpenTelemetry** + **OpenInference** + **Arize Phoenix** for observability. **Pydantic 2.10** validation. **MyPy strict** type checking. **pytest-bdd** for Gherkin BDD tests. **Black** formatter, **Ruff** linter. **pnpm** for frontend. **Pulumi** for Azure IaC.

**Core Philosophy**: Privacy-first, Swiss data sovereignty, security by design, radical transparency through workflow-based agents (not black boxes).

**Three-Tier Architecture**:
- **Tier 1**: Secure LLM access via OpenWebUI chat interface
- **Tier 1+**: Integration with MS Teams, Slack, Outlook (Azure Bot Framework)
- **Tier 2**: AI agents with organizational knowledge (RAG, vector search)
- **Tier 3**: Process orchestration (agents + humans + external systems)

**Swiss AI Agent Protocol**: Internal event-driven protocol governing all communication between platform components. Publish-subscribe model over NATS with strict Control Event (workflow) vs Display Event (observability) separation. Hierarchical scoping (Thread → Display → Run) for security and tracing.

## Repository Structure

**Monorepo**: Single `aihub-core` repository containing all platform code. Open-source and reusable.

**Package Separation**: Code shared by 2+ services belongs in `aihub_lib`. Service-specific code stays in respective packages.

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
- **Swiss AI Agent Protocol**: Internal event-driven communication protocol. NATS publish-subscribe with Control/Display event separation.

## Tech Stack

**Core Platform**:
- **OpenWebUI**: Primary chat interface with dual pipeline architecture (event-based for agents via SSE, OpenAI-compatible for direct model access)
- **LiteLLM**: Universal LLM gateway (unified interface for OpenAI, Anthropic, Google, local models). Cost tracking, request routing, retry policies.
- **Admin UI**: Nuxt.js-based management interface

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
- **Docker Compose**: Multi-environment support (dev, local, nightly, latest, GPU variants). 100% Docker Compose—no separate IaC tooling.
- **Traefik**: Reverse proxy and API gateway
- **OAuth2**: Enterprise authentication (Azure AD with superuser fallback for Docker deployments)

## Coding Style & Conventions

### Type Annotations (MANDATORY)

**ALWAYS type-hint return types:**
```python
def generate_key(user: UserIdentity) -> str:  # ✅ Good
def get_agents(nc: NATS) -> list[AgentDTO]:   # ✅ Good
async def api_key_for_user(user: UserIdentity) -> str:  # ✅ Good

def generate_key(user):  # ❌ Bad - no return type
```

**ALWAYS use `Annotated` for function parameters:**
```python
# ✅ Good - FastAPI dependency injection
def get_agents(
    nc: Annotated[NATS, Depends(use_nats)],
    user: Annotated[UserIdentity, Security(...)],
) -> list[AgentDTO]:
    pass

# ✅ Good - Pydantic Field with validation
class Settings(BaseSettings):
    BASE_URL: Annotated[str, Field(description="The base URL")]
    MAX_BUDGET: Annotated[float | None, Field(description="Budget limit")] = None

# ❌ Bad - no Annotated
def get_agents(nc: NATS, user: UserIdentity):
    pass
```

**Use modern type syntax:**
```python
list[str]          # ✅ Good (Python 3.9+)
List[str]          # ❌ Bad - old syntax

str | None         # ✅ Good (Python 3.10+)
Optional[str]      # ❌ Bad - old syntax

dict[str, int]     # ✅ Good
Dict[str, int]     # ❌ Bad
```

### Pydantic Over Dicts/Dataclasses

**Avoid using raw dicts or dataclasses for structured data. Use Pydantic models:**
```python
# ✅ Good - Pydantic model
class AgentDTO(BaseModel):
    agent_class: str
    agent_id: str
    is_online: bool

# ✅ Good - Pydantic for settings
class LiteLLMProxySettings(EnvironmentSettings):
    BASE_URL: Annotated[str, Field(description="...")]
    API_KEY: Annotated[SecretStr | None, Field(description="...")] = None

# ✅ Good - Pydantic for events
class StartEvent(BaseEvent):
    thread_id: str
    user_id: str

# ❌ Bad - raw dict
def process_agent(agent: dict) -> dict:
    return {"status": agent["status"]}

# ❌ Bad - dataclass when Pydantic is available
@dataclass
class AgentInfo:
    agent_class: str
```

**Why Pydantic?** Automatic validation, serialization, JSON schema generation, environment variable parsing, SecretStr for sensitive data.

### Error Handling: Fail Fast

**Let functions fail. Do NOT wrap large blocks in try-catch:**
```python
# ✅ Good - fail fast
async def api_key_for_user(user: UserIdentity) -> str:
    user_response = await client.get("/user/info", params={"user_id": user.id})
    user_response.raise_for_status()  # Raises HTTPException if failed
    return user_response.json()["key"]

# ✅ Good - validate inputs immediately
def __init__(self, agent_type: type[Agent]):
    if not isinstance(agent_type, type):
        raise ValueError("agent_type must be a class, not an instance.")
    if not issubclass(agent_type, Agent):
        raise ValueError("agent_type must be a subclass of Agent.")

# ❌ Bad - catching and returning None
async def api_key_for_user(user: UserIdentity) -> str | None:
    try:
        user_response = await client.get("/user/info")
        return user_response.json()["key"]
    except Exception:
        return None  # Silently fails!

# ❌ Bad - defensive try-catch wrapper
def process_data(data: dict) -> Result:
    try:
        # 50 lines of logic
        # All wrapped unnecessarily
        return result
    except Exception as e:
        logger.error(f"Failed: {e}")
        return None
```

**Exception**: Only catch exceptions when you have a specific action to take or need to transform the exception.

### Comments & Docstrings

**Comments explain "WHY" (design decisions, context), NOT "WHAT" or "HOW":**
```python
# ✅ Good - explains design rationale
class RunContext(BaseContext):
    """
    A context dedicated to a single run within a thread.

    ### Why RunContext?
    While a thread might have long-lived state, individual runs within
    that thread hold transient data that doesn't need to persist indefinitely.
    By giving each run its own KV store (with a short TTL), RunContext:
    - Ensures data isolation between runs.
    - Reduces clutter by expiring run data after 60 minutes.
    """

# ✅ Good - explains non-obvious decision
# Create new user (not using auto_create_key to control key generation)
await client.post("/user/new", json={"auto_create_key": False, ...})

# ❌ Bad - explains what code does (code is self-documenting)
# Get the user ID
user_id = user.id

# ❌ Bad - redundant comment
# Call the API
response = await client.get("/api/endpoint")

# ❌ Bad - explaining how code works (obvious from code)
# Loop through all agents and filter by access level
return [agent for agent in agents if has_access(agent)]
```

**Docstrings**: Required for all public classes/methods. Explain purpose, design, and usage—not implementation details.

### Async/Await Consistently

**Use async/await whenever interacting with I/O (network, database, Redis):**
```python
# ✅ Good - async for I/O operations
async def api_key_for_user(user: UserIdentity) -> str:
    user_response = await client.get("/user/info")
    key_response = await client.post("/key/generate")
    return key_response.json()["key"]

# ✅ Good - async clients
async def httpx_aclient_for_user(user: UserIdentity) -> httpx.AsyncClient:
    return httpx.AsyncClient(headers={...}, base_url=base_url)

# ❌ Bad - mixing sync and async
async def api_key_for_user(user: UserIdentity) -> str:
    user_response = client.get("/user/info")  # Sync in async function!
    return user_response.json()["key"]
```

### Keep Methods Short & Focused

**Aim for methods under 50 lines. Keep cognitive complexity below 15:**
```python
# ✅ Good - single responsibility, short
@staticmethod
def generate_key_for_user(user: UserIdentity) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(user.id.encode("utf-8"))
    return f"sk-{sha256_hash.hexdigest()[:16]}"

# ✅ Good - endpoint is concise
@router.get("/discover")
async def discover_agents(
    nc: Annotated[NATS, Depends(use_nats)],
    user: Annotated[UserIdentity, Security(...)],
) -> list[AgentDTO]:
    agents = await AgentService.discover_agents(nc)
    return [agent for agent in agents if AccessChecker.from_user(user).has_access(agent)]

# ❌ Bad - too long, doing too much
def process_workflow(data: dict) -> Result:
    # 150 lines of nested logic
    # Multiple responsibilities
    # Hard to test and understand
```

**Refactor**: If a method exceeds 50 lines, extract sub-functions or split responsibilities.

### Class Design & Inheritance

**Use classes for organization, not just for OOP. Use inheritance only when beneficial:**
```python
# ✅ Good - static methods for stateless utilities
class LiteLLMService:
    _user_cache: ClassVar[TTLCache] = TTLCache(maxsize=1024, ttl=21600)

    @staticmethod
    async def api_key_for_user(user: UserIdentity) -> str:
        ...

# ✅ Good - inheritance provides clear benefit (event hierarchy)
class StartEvent(ControlEvent):
    pass

class RunContext(BaseContext):  # Inherits state management logic
    pass

# ❌ Bad - unnecessary inheritance
class UserService(BaseService):  # Adds no value
    pass

# ❌ Bad - over-abstraction with abstract base classes
class AbstractProcessor(ABC):
    @abstractmethod
    def process(self):  # Only one implementation exists
        pass
```

**When to use inheritance:**
- Event hierarchies (BaseEvent → ControlEvent → StartEvent)
- Shared infrastructure (BaseContext, BaseSettings)
- Framework integration (FastAPI Controller, LlamaIndex Workflow)

**When NOT to use inheritance:**
- For code reuse (use composition/utility functions instead)
- Single implementation (use concrete class directly)

### Avoid Premature Optimization

**Focus on readability and maintainability. Optimize only when profiling shows bottlenecks:**
```python
# ✅ Good - simple caching when needed
DISCOVER_AGENTS_CACHE = TTLCache(maxsize=100, ttl=60)

if agent_id in cache:
    return cache[agent_id]

# ✅ Good - straightforward implementation
async def get_agents(nc: NATS) -> list[AgentDTO]:
    agents = await AgentService.discover_agents(nc)
    return [AgentDTO.from_entity(agent) for agent in agents]

# ❌ Bad - premature optimization
# Complex connection pooling, object pools, lazy loading when not needed
```

### Naming Conventions

**Descriptive, explicit names over abbreviations:**
```python
# ✅ Good
not_authorized_to_view_exception = HTTPException(status_code=403, ...)
async def api_key_for_user(user: UserIdentity) -> str:

# ❌ Bad
auth_ex = HTTPException(status_code=403, ...)
async def get_key(u: User) -> str:
```

**Naming rules:**
- `CamelCase` for classes: `AgentController`, `RunContext`, `LiteLLMService`
- `snake_case` for functions/variables: `api_key_for_user`, `thread_id`, `base_url`
- `UPPER_SNAKE_CASE` for constants: `MAX_BUDGET`, `USER_CACHE_TTL`
- Files match class names: `AgentController.py`, `RunContext.py`

### Dependency Injection (FastAPI)

**Use FastAPI's Depends/Security for dependency injection:**
```python
# ✅ Good - type-annotated dependencies
async def get_agents(
    nc: Annotated[NATS, Depends(use_nats)],
    user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
    t: Annotated[LocaleHandler, Depends(use_locale)],
) -> list[AgentDTO]:
    ...

# ❌ Bad - manual dependency instantiation in endpoint
async def get_agents() -> list[AgentDTO]:
    nc = await connect_to_nats()  # Should be dependency
    user = get_current_user()     # Should be dependency
```

### Modern Python Features

**Use Python 3.10+ features:**
```python
# ✅ Good - union with |
def process(value: str | int | None) -> dict | None:
    pass

# ✅ Good - @property for computed attributes
@property
def event_name(self) -> str:
    return self.__class__.__name__

# ✅ Good - @override decorator (Python 3.12+)
@override
def process(self) -> Result:
    pass

# ✅ Good - match/case for complex conditionals (Python 3.10+)
match event_type:
    case "start":
        return StartEvent()
    case "stop":
        return StopEvent()

# ❌ Bad - old Optional syntax
from typing import Optional
def process(value: Optional[str]) -> Optional[dict]:
    pass
```

### Code Organization & Architecture

**Follow Controller → Service → Entity pattern:**
```python
# Controller (HTTP layer, validation, auth)
class AgentController(Controller):
    @router.get("/discover")
    async def discover_agents(user: UserIdentity) -> list[AgentDTO]:
        agents = await AgentService.discover_agents(nc)  # Delegate to service
        return [agent for agent in agents if has_access(user, agent)]

# Service (business logic, orchestration)
class AgentService:
    @staticmethod
    async def discover_agents(nc: NATS) -> list[AgentEntity]:
        # NATS discovery, caching, transformation
        return await _discover_via_nats(nc)

# Entity (data persistence)
class AgentEntity(Document):
    agent_class: str
    agent_id: str
    meta = {"collection": "agents"}
```

**Separation of concerns:**
- Controllers: HTTP/WebSocket handling, auth, input validation
- Services: Business logic, orchestration, external API calls
- Entities: Database models, persistence logic
- DTOs: Data transfer between layers (Pydantic models)

### Summary: Key Principles

1. ✅ **Type-hint everything**: Return types, `Annotated` parameters, modern syntax (`|`, not `Optional`)
2. ✅ **Pydantic for structured data**: Avoid raw dicts/dataclasses
3. ✅ **Fail fast**: Immediate validation, let exceptions propagate
4. ✅ **Comments explain "why"**: Never "what" or "how"
5. ✅ **Async consistently**: All I/O operations use async/await
6. ✅ **Keep methods short**: < 50 lines, cognitive complexity < 15
7. ✅ **Inheritance only when beneficial**: Events, base classes, frameworks
8. ✅ **No premature optimization**: Readability first, optimize when proven necessary
9. ✅ **Descriptive naming**: `not_authorized_to_view_exception` not `auth_ex`
10. ✅ **Modern Python**: Use Python 3.10+ features (`|`, `@property`, `@override`)

## Coding Conventions (Tools)

**Python** (Backend):
- **Formatter**: Black (line length: 120). Config: `/home/user/aihub-core/pyproject.toml`
- **Linter**: Ruff (rules: E, F, UP, I). Config: `/home/user/aihub-core/pyproject.toml`
- **Type Checker**: MyPy (`strict = true`). Config: `/home/user/aihub-core/pyproject.toml`
- **Naming**: `snake_case` for files/dirs, `CamelCase` for classes, `test_*.py` for tests

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
- **Branching**: `main` branch only. Feature branches: `<type>/short-description` (`feat/`, `fix/`, `chore/`, `test/`, `doc/`)
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

**CRITICAL**: Consult existing ADRs before significant changes. Located: `/home/user/aihub-core/aihub_doc/arc42/decisions/`

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
- **Markers**: `@pytest.mark.azure`, `@pytest.mark.slow`, `@pytest.mark.integration` (defined in `pyproject.toml`)
- **BDD**: Use `pytest-bdd` for agent/process workflows (Gherkin `.feature` files in `tests/features/`)
- **Async**: pytest-bdd has limitations; use plain pytest for async tests
- **Run**: `make test` (within Poetry shell)

**Philosophy**: Pragmatic, not TDD. Write tests when straightforward. MUST run all tests before commit.

## MCP Integration (AI Assistant Context)

**Model Context Protocol**: Provides AI assistants (Claude Code, Gemini CLI) with development environment access.

**Config**: `/home/user/aihub-core/.mcp.json`

**MCP Servers**:
- **Phoenix MCP**: AI observability/tracing data (http://localhost:6006)
- **MongoDB MCP**: Read-only database access (mongodb://admin:admin@localhost:27017/aihub)
- **AI-Hub API MCP**: API endpoint testing (http://localhost:8000/mcp)

## Quick Reference

**Essential Files**:
- Root README (human-friendly): `/home/user/aihub-core/README.md`
- Docker Compose (dev): `/home/user/aihub-core/docker-compose.dev.yml`
- Env config: `/home/user/aihub-core/.env` (copy from `.env.dev`)
- Makefile (per scope): `/home/user/aihub-core/<scope>/Makefile`
- ADRs: `/home/user/aihub-core/aihub_doc/arc42/decisions/`
- Architecture docs: `/home/user/aihub-core/aihub_doc/docs/2_platform/2_architecture/`
- Swiss AI Agent Protocol: `/home/user/aihub-core/aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/index.en.md`

**Common Commands** (within scope dir, Poetry shell activated):
- `poetry install`: Install dependencies
- `poetry add <pkg>`: Add dependency
- `make format`: Run Black formatter
- `make lint`: Run Ruff + MyPy
- `make pr-ready`: Format + lint with auto-fix (RUN BEFORE COMMIT)
- `make test`: Run pytest suite (RUN BEFORE COMMIT)

**Access Points** (docker-compose.dev.yml):
- OpenWebUI: http://localhost:3000
- Admin UI: http://localhost:3001
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dagster: http://localhost:3002
- Phoenix: http://localhost:6006
- SeaweedFS: http://localhost:8889

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

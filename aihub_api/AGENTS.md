# aihub_api - REST API & WebSocket Gateway

**Purpose**: Main user-facing REST API (FastAPI) + WebSocket gateway. Connects frontend to AI-Hub services.

Tech Stack & Paradigms: FastAPI REST API with async support. uvicorn + gunicorn ASGI servers. Azure Identity + Azure mgmt SDKs (Cosmos, resources). OAuth2/OpenID Connect (custom implementation). cryptography + PyJWT for token handling. httpx async HTTP client. NATS pub-sub for agent communication. MongoEngine for persistence. python-multipart for file uploads. pydub + audioop-lts for audio processing (Python 3.13 compat). LlamaIndex text-embeddings-inference for embeddings. Arize Phoenix observability. fastmcp for Model Context Protocol server. OpenTelemetry FastAPI instrumentation. Jambo (external lib from bbvch-ai). cachetools TTLCache. Controller-Service-DTO pattern. Pydantic v2 validation. OpenAPI/Swagger auto-docs. Hierarchical permissions (aihub.user.resource.action). ApiRunner and ApiTestRunner. pytest-bdd + asgi-lifespan for testing.

## Scope Responsibility

HTTP endpoints, real-time WebSocket communication, agent/process discovery, thread management, authentication enforcement. NOT business logic (delegate to services).

## Folder Structure

```
aihub_api/
├── routes/                    # Controllers + Services + DTOs (by domain)
│   ├── agent/                 # Agent management endpoints
│   ├── thread/                # Thread/conversation management
│   ├── user/                  # User management
│   ├── openai/                # OpenAI-compatible API
│   └── ...                    # Other domain routes
├── sockets/                   # WebSocket connection management
├── runners/                   # ApiRunner, ApiTestRunner
├── pagination/                # PageNumber, PageSize types
└── playground/testing/        # Test server with frontend
```

## Key Pattern: Controller-Service-DTO-Entity

**Controller**: HTTP endpoint definition, auth/validation, routing.
**Service**: Business logic, external system integration (NATS, DB via Entities).
**DTO**: Pydantic models for request/response validation + docs.
**Entity**: MongoDB document schema + repository methods (lives in `aihub_lib/persistence/`, shared across services).

### Example Structure

```python
# Controller (routes/my_domain/MyController.py)
class MyController(Controller):
    def create_resource(self, route: str = "/") -> "MyController":
        @self.router.post(route, tags=self.tags)
        async def create_resource(request: MyRequestDTO, ...) -> MyResponseDTO:
            return await MyService.create_resource(request, t)
        return self

# Service (routes/my_domain/MyService.py)
class MyService:
    @staticmethod
    async def create_resource(request: MyRequestDTO, t: LocaleHandler) -> MyResponseDTO:
        entity = MyResourceEntity.create_resource(name=request.name)  # Use Entity
        return MyResponseDTO(id=str(entity.id), name=entity.name)

# Entity (aihub_lib/persistence/my_domain/MyResourceEntity.py) - Repository pattern
class MyResourceEntity(Document):
    meta = {"collection": "my_resources"}
    name = StringField(required=True)

    @classmethod  # Repository methods as classmethods
    def create_resource(cls, name: str) -> "MyResourceEntity": ...
```

**CRITICAL**: Register controllers in `/home/user/aihub-core/aihub_api/app/main.py`:

```python
from aihub_api.routes.my_domain.MyController import MyController
runner.mount(MyController(auth=auth).create_resource().get_resource())
```

## Authentication & Authorization

**Permission Format**: `aihub.[user|admin].<resource>.<subresource>.<id>`

**Common Patterns**:

- `aihub.user.?>`: General user access
- `aihub.user.agent.{agent_class}.{agent_id}`: Specific agent
- `aihub.admin.service.roles`: Admin service access

**Dynamic Checks**: Use `AccessChecker.from_user(user).has_access_to_agent()` in services.

## Pagination

**Standard Pattern**:

```python
def get_resources(
    page: PageNumber = 1,  # Defaults to 1
    page_size: PageSize = 20,  # Defaults to 20, max varies
) -> PaginatedResourcesResponse:
    total, resources = await Service.get_paginated(page, page_size)
    return PaginatedResourcesResponse(resources=resources, total=total, page=page, page_size=page_size)
```

## Agent Communication Bridge

**Purpose**: Bridge between Swiss AI Agent Protocol (NATS events) and external protocols (OpenAI, WebSocket, SSE).

### How It Works

**Outbound (API → Agents)**:

- `ExternalAgentEventDistributor` publishes events to NATS via `AgentThreadTopicManager`
- Agents subscribe to thread-specific subjects and process events

**Inbound (Agents → API)**:

- Agents publish `DisplayEvent`s to NATS
- API subscribes with TWO parallel handlers:
  - `EventPersister`: Persists ALL events to MongoDB (audit/history)
  - `WebSocketSender`: Broadcasts to connected WebSocket clients in real-time

**Protocol Conversion**:

- **WebSocket**: Events wrapped in `ContextualizedAgentEvent` (adds agent_class, thread_id context), sent as JSON
- **SSE (OpenAI streaming)**: Events queued, converted to `ChatCompletionChunk`, streamed as `data: {...}\n\n`
- **Aggregated JSON**: Events collected, aggregated, returned as complete `ChatCompletion` response

### Key Files

- Discovery: `/home/user/aihub-core/aihub_api/aihub_api/routes/agent/AgentService.py` (L113-246, L447-551)
- SSE streaming: `/home/user/aihub-core/aihub_api/aihub_api/routes/openai/OpenaiService.py` (L342-423)
- WebSocket: `/home/user/aihub-core/aihub_api/aihub_api/sockets/manager/WebSocketManager.py`
- Event wrapping: `/home/user/aihub-core/aihub_api/aihub_api/sockets/events/server_to_user/ContextualizedAgentEvent.py`
- Lifecycle/wiring: `/home/user/aihub-core/aihub_api/aihub_api/runners/lifetime/lifetime_manager.py` (L84-111)

## Testing

### Test Types

**1. Controller/API Tests** (HTTP-level with `AsyncClient`):

- Test status codes, auth, response structure
- Use `ApiTestRunner` or `SimulatedAgentApiTestRunner` (for agent interactions)
- Location: `playground/testing/tests/<domain>/test_*_api.py`

**2. Service Tests** (unit tests with mocked NATS/DB):

- Test business logic in isolation
- Mock `AgentEntity`, NATS subscribers, discovery responses
- Location: `playground/testing/tests/<domain>/test_*_service_unit_tests.py`

**3. Integration Tests** (with simulated agents):

- Test full agent interaction flow (send event → receive response)
- Use `SimulatedAgentApiTestRunner` to simulate agent behavior over NATS
- Tests discovery, event distribution, response aggregation

### Basic Setup

```python
# Simple controller test
@pytest_asyncio.fixture
async def client():
    auth = DangerousDevelopmentOnlyAuthHandler()
    runner = ApiTestRunner()
    runner.mount(MyController(auth=auth).create_resource())
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test") as client:
            yield client

# Test with simulated agent
@pytest_asyncio.fixture
async def agent_client():
    runner = SimulatedAgentApiTestRunner(agent_class="TestAgent", agent_id="test_1")
    runner.with_simple_chunk_events()  # Simulate agent responses
    await runner.start_simulation()
    # ... mount controllers, create app, yield client
```

### Key Fixtures & Utilities

- `DangerousDevelopmentOnlyAuthHandler`: Bypass auth for testing
- `mock_role_entity_methods`: Mock role/permission checks
- `enable_logging()`: Enable debug logs in tests
- `AgentService._clear_cache()`: Clear discovery cache between tests

### Example Test Files

- API test: `playground/testing/tests/agent/test_agent_api.py`
- Service test: `playground/testing/tests/agent/test_agent_service_unit_tests.py`
- Integration test: `playground/testing/tests/agent/test_agent_api_with_custom_event.py`
- Simulated runner: `aihub_api/runners/simulation/agent/SimulatedAgentApiTestRunner.py`

## Playground

**Location**: `/home/user/aihub-core/aihub_api/playground/testing/`
**Start**: `cd playground/testing && python main.py`
**Access**: http://localhost:8000 (frontend), http://localhost:8000/api/v1/docs (Swagger)

## Pre-Commit

```bash
make pr-ready  # Format + lint
make test      # Run tests
```

## Essential Files

- Base controller: `/home/user/aihub-core/aihub_lib/aihub_lib/routes/Controller.py`
- Playground main: `/home/user/aihub-core/aihub_api/playground/testing/main.py`
- Example controller: `/home/user/aihub-core/aihub_api/routes/agent/AgentController.py`
- Example service: `/home/user/aihub-core/aihub_api/routes/agent/AgentService.py`
- WebSocket manager: `/home/user/aihub-core/aihub_api/sockets/manager/`

## Quick Reference

**New endpoint workflow**:

1. Create DTOs in `routes/my_domain/dto/`
2. Create Service in `routes/my_domain/MyService.py` (`@staticmethod` methods)
3. Create Controller in `routes/my_domain/MyController.py` (fluent API: `.create_resource().get_resource()`)
4. Mount in runner: `runner.mount(MyController(auth=auth).create_resource())`
5. Test: `pytest playground/testing/tests/`
6. Interactive test: Add to `playground/testing/main.py`, run, access http://localhost:8000

**Error handling**: Raise `HTTPException(status_code=..., detail=...)`. Let unexpected errors propagate to FastAPI middleware.

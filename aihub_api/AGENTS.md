# aihub_api - REST API & WebSocket Gateway

**Purpose**: Main user-facing REST API (FastAPI) + WebSocket gateway. Connects frontend to AI-Hub services.

**Tech Stack & Paradigms**: FastAPI REST API with async support. OAuth2/OpenID Connect authentication (Azure AD integration). Controller-Service-DTO architectural pattern. WebSocket support via Socket.IO. NATS pub-sub for agent communication. Pydantic models for request/response validation. TTLCache for in-memory caching. Hierarchical permission system (aihub.user.resource.action). OpenAPI/Swagger auto-generated docs. Dependency injection with FastAPI Depends. PageNumber/PageSize types for pagination. ApiRunner and ApiTestRunner for testing.

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

## Key Pattern: Controller-Service-DTO

**Controller**: HTTP endpoint definition, auth/validation, routing.
**Service**: Business logic, external system integration (NATS, DB).
**DTO**: Pydantic models for request/response validation + docs.

### Example Structure

```python
# Controller (routes/my_domain/MyController.py)
class MyController(Controller):
    def create_resource(self, route: str = "/") -> "MyController":
        @self.router.post(route, tags=self.tags)
        async def create_resource(
            request: MyRequestDTO,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.my-domain.create"))],
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)]
        ) -> MyResponseDTO:
            return await MyService.create_resource(nc, request, t)
        return self

# Service (routes/my_domain/MyService.py)
class MyService:
    @staticmethod
    async def create_resource(nc: NATS, request: MyRequestDTO, t: LocaleHandler) -> MyResponseDTO:
        # Business logic here
        pass

# DTO (routes/my_domain/dto/MyRequestDTO.py)
class MyRequestDTO(BaseModel):
    name: Annotated[str, Field(description="Resource name")]
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

## Caching

**TTLCache Pattern**:
```python
from cachetools import TTLCache

CACHE = TTLCache(maxsize=100, ttl=300)  # 5 min, 100 items

async def get_resource(id: str):
    if id in CACHE:
        return CACHE[id]
    resource = await fetch_resource(id)
    CACHE[id] = resource
    return resource
```

## WebSocket Integration

**Purpose**: Real-time event streaming (chat, agent events, live updates).

**Pattern**: `WebSocketManager` handles connection lifecycle, broadcasts to subscribed clients.

## NATS Integration

**Agent Communication**: `AgentThreadTopicManager` for routing to agents.
**Discovery**: Broadcast requests → collect responses → filter by user permissions.

## Testing

**Controller Tests**: HTTP-level (FastAPI TestClient). Focus on status codes, auth, response structure.
**Service Tests**: Business logic with mocked dependencies.

**Test Client**:
```python
@pytest.fixture
def client():
    runner = ApiTestRunner()
    runner.mount(MyController(auth=DangerousDevelopmentOnlyAuthHandler()).create_resource())
    return TestClient(runner.create_app())
```

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

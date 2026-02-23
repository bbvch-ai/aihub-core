---
title: AI-Hub API
index: 4
---

# 🚀 AI-Hub API Developer's Guide

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_api-core&metric=alert_status&token=0813ff21e25c4e60e66e06acaefd2927ba63e897)](https://sonarcloud.io/summary/new_code?id=aihub-core_api-core)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_api-core&metric=security_rating&token=0813ff21e25c4e60e66e06acaefd2927ba63e897)](https://sonarcloud.io/summary/new_code?id=aihub-core_api-core)

[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_api-core&metric=vulnerabilities&token=0813ff21e25c4e60e66e06acaefd2927ba63e897)](https://sonarcloud.io/summary/new_code?id=aihub-core_api-core)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_api-core&metric=sqale_rating&token=0813ff21e25c4e60e66e06acaefd2927ba63e897)](https://sonarcloud.io/summary/new_code?id=aihub-core_api-core)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_api-core&metric=ncloc&token=0813ff21e25c4e60e66e06acaefd2927ba63e897)](https://sonarcloud.io/summary/new_code?id=aihub-core_api-core)

## 1. 🎯 Foundational Knowledge of API Development

This section covers the foundational architecture, patterns, and terminology you need to know before building API endpoints.

::: info
This documentation assumes you have completed the general AI-Hub setup as described in the main README.md. Make sure you have the required infrastructure running before proceeding.
:::

### 📚 Introduction to `aihub_api`

You are contributing to the **aihub_api** scope, which contains the main user-facing REST API (FastAPI) and WebSocket gateway within the AI-Hub platform. This scope implements HTTP endpoints and real-time communication that connect frontend applications to the underlying AI-Hub services.

### 📁 Project Structure

The `aihub_api` scope is organized as follows:

```
aihub_api/
├── aihub_api/                 # Main package source
│   ├── routes/                # HTTP endpoint controllers and services
│   │   ├── agent/             # Agent management endpoints
│   │   ├── thread/            # Thread/conversation management
│   │   ├── user/              # User management endpoints
│   │   ├── openai/            # OpenAI-compatible API endpoints
│   │   └── ...                # Other domain-specific routes
│   ├── sockets/               # WebSocket management and events
│   │   ├── manager/           # WebSocket connection management
│   │   └── sender/            # WebSocket message sending
│   ├── runners/               # API server runners and test infrastructure
│   ├── pagination/            # Pagination utilities and types
│   ├── i18n/                  # API internationalization
│   └── testing/               # API testing utilities
└── playground/                # Examples and testing - START HERE
    ├── testing/               # Test API server with frontend
    └── development/           # Development utilities
```

### 🏗️ The Controller-Service-DTO Pattern

::: info Architecture Pattern
The API follows a layered architecture with clear separation of concerns:
:::

```python
# Controller - HTTP endpoint definition using factory pattern
class AgentController(Controller):
    def discover_agents(self, route: str = "/discover") -> "AgentController":
        @self.router.get(route, tags=self.tags)
        async def discover_agents(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)]
        ) -> list[AgentDTO]:
            agents = await AgentService.discover_agents(nc, t)
            return [agent for agent in agents if AccessChecker.from_user(user).has_access_to_agent(agent.agent_class, agent.agent_id)]
        return self

# Service - Business logic implementation
class AgentService:
    @staticmethod
    async def discover_agents(nc: NATS, t: LocaleHandler) -> list[AgentDTO]:
        # NATS-based agent discovery logic
        # Caching and data processing
        return agents

# DTO - Data structure definition
class AgentDTO(BaseModel):
    agent_class: Annotated[str, Field(description="The agent's class identifier")]
    agent_id: Annotated[str, Field(description="Unique identifier for the agent instance")]
    agent_config: Annotated[AgentConfigDTO, Field(description="Configuration details of the agent")]
```

::: tip Key Principles
- **Controllers** handle HTTP concerns (routing, authentication, validation)
- **Services** contain business logic and external system integration
- **DTOs** define data structures with validation and documentation
- **Clear boundaries** between layers for maintainability and testing
:::

### ⚡ FastAPI Integration

::: info FastAPI Benefits
The API is built on FastAPI, providing:
:::

**Automatic Documentation:**

- OpenAPI/Swagger UI at `/docs`
- ReDoc documentation at `/redoc`
- JSON schema generation from Pydantic models

**Dependency Injection:**

- NATS client injection via `use_nats`
- User authentication via `Security()`
- Locale handling via `use_locale`

**WebSocket Support:**

- Real-time event streaming
- Connection management
- Message routing

---

## 2. 🚀 The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging API endpoints.

### ⚙️ Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

::: warning
Always activate the Poetry environment before working. All subsequent commands must be run from within this activated shell.
:::

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

```bash
cd aihub_api
poetry shell
```

### 🛠️ Step 1: Create Controller, Service, and DTOs

::: info
Follow this three-part process to define a new API endpoint domain. Each part builds on the previous one to create a complete API implementation.
:::

1. **Create the DTO Models**: Define the data structures for requests and responses.

   ```python
   # my_domain/dto/MyRequestDTO.py
   from typing import Annotated
   from pydantic import BaseModel, Field

   class MyRequestDTO(BaseModel):
       name: Annotated[str, Field(description="Name of the resource")]
       description: Annotated[str | None, Field(description="Optional description")] = None

   class MyResponseDTO(BaseModel):
       id: Annotated[str, Field(description="Unique identifier")]
       name: Annotated[str, Field(description="Name of the resource")]
       created_at: Annotated[str, Field(description="Creation timestamp")]
   ```

2. **Create the Service**: Implement the business logic layer.

   ```python
   # my_domain/MyService.py
   from aihub_lib.i18n.LocaleHandler import LocaleHandler
   from nats.aio.client import Client as NATS

   class MyService:
       @staticmethod
       async def create_resource(nc: NATS, request: MyRequestDTO, t: LocaleHandler) -> MyResponseDTO:
           # Business logic implementation
           # External system integration
           # Data processing
           return MyResponseDTO(id="123", name=request.name, created_at="2024-01-01")

       @staticmethod
       async def get_resource(nc: NATS, resource_id: str, t: LocaleHandler) -> MyResponseDTO:
           # Resource retrieval logic
           pass
   ```

3. **Create the Controller**: Define the HTTP endpoints.

   ```python
   # my_domain/MyController.py
   from typing import Annotated
   from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
   from aihub_lib.auth.identity.UserIdentity import UserIdentity
   from aihub_lib.i18n.LocaleHandler import LocaleHandler
   from aihub_lib.i18n.LocaleString import LocaleString
   from aihub_lib.nats.dependencies.use_nats import use_nats
   from aihub_lib.routes.Controller import Controller
   from fastapi import Depends, Security
   from nats.aio.client import Client as NATS

   class MyController(Controller):
       name = LocaleString(en="My Domain")
       description = LocaleString(en="Manages my domain resources")
       icon = "my-icon"

       def __init__(self, *, auth: AuthHandler, route: str = "/my-domain"):
           super().__init__(auth=auth, route=route)

       def create_resource(self, route: str = "/") -> "MyController":
           @self.router.post(route, tags=self.tags)
           async def create_resource(
               request: MyRequestDTO,
               nc: Annotated[NATS, Depends(use_nats)],
               user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.my-domain.create"))],
               t: Annotated[LocaleHandler, Depends(use_locale)]
           ) -> MyResponseDTO:
               return await MyService.create_resource(nc, request, t)
           return self

       def get_resource(self, route: str = "/{resource_id}") -> "MyController":
           @self.router.get(route, tags=self.tags)
           async def get_resource(
               resource_id: str,
               nc: Annotated[NATS, Depends(use_nats)],
               user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.my-domain.read"))],
               t: Annotated[LocaleHandler, Depends(use_locale)]
           ) -> MyResponseDTO:
               return await MyService.get_resource(nc, resource_id, t)
           return self
   ```

### 🧪 Step 2: Write and Run Tests

::: tip API Testing
API testing uses pytest with FastAPI's test client and the `ApiTestRunner` or `SimulatedAgentApiTestRunner`.
:::

1. **Create Test Files**: Write comprehensive tests for your endpoints.

   ```python
   # playground/testing/tests/my_domain/test_my_domain_api.py
   import pytest
   from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
       DangerousDevelopmentOnlyAuthHandler,
   )
   from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
       DangerousDevelopmentOnlyIdentityProvider,
   )
   from fastapi.testclient import TestClient
   from httpx import AsyncClient
   from asgi_lifespan import LifespanManager
   from httpx import ASGITransport

   from aihub_api.runners.ApiTestRunner import ApiTestRunner
   from aihub_api.routes.my_domain.MyController import MyController

   # For synchronous tests (simple HTTP endpoints)
   @pytest.fixture
   def api_client():
       """Fixture to create a test client for the API."""
       auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
       runner = ApiTestRunner()
       runner.mount(MyController(auth=auth).create_resource().get_resource())
       return TestClient(runner.create_app())

   # For asynchronous tests (with real event handling)
   @pytest.fixture
   async def async_api_client():
       """Fixture to create an async test client for the API."""
       auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
       runner = ApiTestRunner()
       runner.mount(MyController(auth=auth).create_resource().get_resource())
       app = runner.create_app()
       
       async with LifespanManager(app) as lifespan:
           async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1") as client:
               yield client

   def test_create_resource(api_client):
       """Test resource creation with synchronous client."""
       response = api_client.post("/my-domain/", json={
           "name": "Test Resource",
           "description": "Test description"
       })
       assert response.status_code == 201
       data = response.json()
       assert data["name"] == "Test Resource"
       assert "id" in data

   @pytest.mark.asyncio
   async def test_get_resource(async_api_client):
       """Test resource retrieval with asynchronous client."""
       # First create a resource
       create_response = await async_api_client.post("/my-domain/", json={"name": "Test Resource"})
       resource_id = create_response.json()["id"]
       
       # Then retrieve it
       response = await async_api_client.get(f"/my-domain/{resource_id}")
       assert response.status_code == 200
       data = response.json()
       assert data["id"] == resource_id
   ```

2. **Run Tests**: Execute tests from your activated Poetry shell.

   ```bash
   # Run all tests
   poetry run pytest

   # Run specific test file
   poetry run pytest playground/testing/tests/my_domain/test_my_domain_api.py

   # Run with coverage
   make test-cov
   ```

### 🎮 Step 3: Test with Playground

::: info
The playground provides a full API server with frontend for interactive testing.
:::

1. **Update Playground Configuration**: Add your controller to the test server.

   ```python
   # playground/testing/main.py
   from aihub_api.routes.my_domain.MyController import MyController

   async def main():
       runner = SimulatedAgentApiTestRunner(
           agent_class="test_agent",
           agent_id="test_agent_id",
       )
       
       auth = DangerousDevelopmentOnlyAuthHandler(
           identity_provider=DangerousDevelopmentOnlyIdentityProvider()
       )
       
       runner.mount(
           # ... existing controllers ...
           MyController(auth=auth).create_resource().get_resource(),
       )
       
       await runner.run()
   ```

2. **Start the Test Server**: Run the playground server.

   ```bash
   cd playground/testing
   python main.py
   ```

3. **Access the API**:

   - **Frontend**: `http://localhost:8000` (interactive testing interface)
   - **API Docs**: `http://localhost:8000/api/v1/docs` (Swagger UI)
   - **ReDoc**: `http://localhost:8000/api/v1/redoc` (Alternative API docs)
   - **Langfuse Traces**: `http://localhost:6006` (agent execution traces)

4. **Test with curl/wget**: You can use curl or wget to make requests to API endpoints:

   ```bash
   # Check if API is running
   curl http://localhost:8000/api/v1/health

   # Get OpenAPI schema to see all endpoints
   curl http://localhost:8000/openapi.json

   # Test agent discovery endpoint
   curl http://localhost:8000/api/v1/agents/discover

   # Test specific agent endpoint
   curl http://localhost:8000/api/v1/agents/my_agent_class/my_agent_id
   ```

::: warning Authentication for Testing
For curl/wget testing to work, you **MUST** set the auth in `main.py` to `DangerousDevelopmentOnlyAuthHandler` and `DangerousDevelopmentOnlyIdentityProvider` to bypass oauth2 authentication (this is already configured in the playground).
:::

### 🔍 Step 4: Debug and Observe Your API

::: tip Enable Logging
Add logging to your API development.
:::

```python
# Add to your main.py or test files
from aihub_lib.infrastructure.logging.logger import enable_logging
enable_logging()
```

::: tip Key Debugging Tools
- **FastAPI Docs**: Interactive API testing at `/docs`
- **Network Tab**: Browser developer tools for HTTP requests
- **Logs**: Structured logging for request/response debugging
- **Langfuse Traces**: Agent interaction visualization
:::

::: warning Common Debugging Patterns
- Check NATS connection status and message flow
- Verify authentication and permission issues
- Test with different user roles and permissions
:::

### ✅ Step 5: Ensure Code Quality

::: warning
Before committing your changes, use the provided Makefile commands.
:::

```bash
# Run this before creating a pull request
make pr-ready

# Or run commands individually
make format      # Ruff formatting
make lint        # Ruff linting
```

::: danger
All API code must use strict Python type annotations and follow the Controller-Service-DTO pattern. This is enforced by CI/CD.
:::

---

## 3. 🎨 API Design Patterns and Best Practices

This section covers common patterns and best practices for building robust API endpoints.

### 🔐 Authentication and Authorization Patterns

::: info Permission System
The AI-Hub uses a sophisticated hierarchical permission system with wildcards and implicit checks. All permissions follow the format: `aihub.[user|admin].<resource_type>.<resource_subtype>.<resource_id>.[...]`
:::

#### 🔐 Permission-Based Access Control

```python
class SecureController(Controller):
    def protected_endpoint(self, route: str = "/protected") -> "SecureController":
        @self.router.get(route, tags=self.tags)
        async def protected_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)]
        ) -> dict:
            return {"message": "Access granted", "user_id": user.id}

        return self

    def agent_specific_endpoint(self, route: str = "/{agent_class}/{agent_id}") -> "SecureController":
        @self.router.get(route, tags=self.tags)
        async def agent_specific_endpoint(
            agent_class: str,
            agent_id: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))],
            t: Annotated[LocaleHandler, Depends(use_locale)]
        ) -> dict:
            return {"message": "Access granted to specific agent", "agent_class": agent_class, "agent_id": agent_id}

        return self

    def admin_endpoint(self, route: str = "/admin") -> "SecureController":
        @self.router.get(route, tags=self.tags)
        async def admin_endpoint(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.service.my_service"))],
            t: Annotated[LocaleHandler, Depends(use_locale)]
        ) -> dict:
            return {"message": "Admin access granted"}
        return self
```

#### 📝 Common Permission Patterns

```python
# General user access (most common)
"aihub.user.?>"  # User has access to any user-level resource

# Agent-specific access
"aihub.user.agent.{agent_class}.{agent_id}"  # Access to specific agent
"aihub.user.agent.?>"  # Access to any agent (implicit check)

# Admin service access
"aihub.admin.service.roles"  # Admin access to roles service
"aihub.admin.agent.?>"  # Admin access to any agent

# Wildcard Examples:
# User access rule: "aihub.user.agent.my_class.*" matches "aihub.user.agent.my_class.instance_123"
# User access rule: "aihub.user.agent.>" matches any agent resource at any level
```

#### 🔄 Dynamic Permission Checking with AccessChecker

::: tip Dynamic Permission Checks
While controller endpoints handle most permission checks via the `@Security` decorator, sometimes you need to perform dynamic permission checks within service methods. The `AccessChecker` class provides programmatic access to the permission system, allowing you to check permissions based on runtime values or implement more complex authorization logic.
:::

```python
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel

# In Service layer
class ResourceService:
    @staticmethod
    async def get_resource(user: UserIdentity, agent_class: str, agent_id: str) -> ResourceDTO:
        # Direct access check - returns boolean
        if not AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Alternative: Check access level for conditional logic
        access_level = AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id)
        if access_level == AccessLevel.ACCESS_DENIED:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Use access level to filter results (admin vs user view)
        if access_level == AccessLevel.ACCESS_ADMIN:
            return await retrieve_full_resource(agent_class, agent_id)
        else:
            return await retrieve_user_filtered_resource(agent_class, agent_id, user.id)
```

### 📊 Pagination Patterns

::: info Pagination System
The API uses a consistent pagination approach across all endpoints that return lists of resources. The pagination system uses `PageNumber` and `PageSize` types to ensure type safety and validation, with reasonable defaults and limits to prevent abuse.
:::

#### 📊 Standard Pagination

```python
class ListController(Controller):
    def get_resources(self, route: str = "/") -> "ListController":
        @self.router.get(route, tags=self.tags)
        async def get_resources(
            page: PageNumber = 1,
            page_size: PageSize = 20,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)]
        ) -> PaginatedResourcesResponse:
            # Service layer handles the actual pagination logic
            total, resources = await ResourceService.get_paginated_resources(
                page=page, page_size=page_size, user_id=user.id, t=t
            )
            
            # Calculate total pages for client convenience
            total_pages = (total + page_size - 1) // page_size
            
            return PaginatedResourcesResponse(
                resources=resources,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        return self
```

### 🚨 Error Handling Patterns

::: warning Error Handling Philosophy
The AI-Hub API follows a "fail fast" philosophy - we don't wrap everything in try-except blocks but rather let errors propagate naturally. Controllers and Services always raise `HTTPException` for client errors and let unexpected exceptions bubble up to FastAPI's error handling middleware.
:::

#### 📝 Structured Error Responses

```python
from fastapi import HTTPException

class ErrorHandlingService:
    @staticmethod
    async def safe_operation(resource_id: str) -> ResourceDTO:
        # Let most errors propagate naturally
        resource = await external_service.get_resource(resource_id)
        
        # Only catch specific expected errors and convert to HTTP errors
        if not resource:
            raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")
        
        return ResourceDTO.from_external(resource)
    
    @staticmethod
    async def operation_with_external_dependency(resource_id: str) -> ResourceDTO:
        try:
            return await external_service.get_resource(resource_id)
        except ExternalServiceError as e:
            # Re-raise as HTTPException for client consumption
            raise HTTPException(status_code=503, detail=f"External service unavailable: {str(e)}")
        # Let unexpected errors bubble up - FastAPI will handle them
```

### 💾 Caching Patterns

::: tip Caching Strategy
The API uses in-memory caching to reduce load on external services like NATS and databases. The `TTLCache` from `cachetools` is the standard choice, providing automatic expiration and memory management. Caching is typically implemented at the service layer to benefit all endpoints.
:::

#### ⏰ TTL-Based Caching

```python
from cachetools import TTLCache

# Service-level caching - shared across all endpoint calls
RESOURCE_CACHE = TTLCache(maxsize=100, ttl=300)  # 5 minutes, 100 items max

class CachedService:
    @staticmethod
    async def get_resource(resource_id: str) -> ResourceDTO:
        # Check cache first
        if resource_id in RESOURCE_CACHE:
            return RESOURCE_CACHE[resource_id]
        
        # Fetch from external service if not cached
        resource = await expensive_operation(resource_id)
        
        # Cache the result
        RESOURCE_CACHE[resource_id] = resource
        return resource
    
    @staticmethod
    def clear_cache() -> None:
        """Clear cache for testing or maintenance."""
        RESOURCE_CACHE.clear()
```

### 🔌 WebSocket Integration Patterns

::: info WebSocket Usage
WebSockets provide real-time communication between the frontend and backend, primarily used for streaming events and live updates. The WebSocket manager handles connection lifecycle, message broadcasting, and maintains client subscriptions to specific threads or topics.
:::

#### 🔴 Real-time Event Streaming

```python
class EventController(Controller):
    def websocket_endpoint(self, route: str = "/ws") -> "EventController":
        @self.router.websocket(route)
        async def websocket_endpoint(
            websocket: WebSocket,
            ws_manager: Annotated[WebSocketManager, Depends(use_ws_manager)]
        ):
            # Register the WebSocket connection
            await ws_manager.connect(websocket)
            try:
                while True:
                    # Listen for incoming messages from client
                    data = await websocket.receive_text()
                    # Broadcast to all connected clients
                    await ws_manager.broadcast(f"Echo: {data}")
            except WebSocketDisconnect:
                # Clean up when client disconnects
                await ws_manager.disconnect(websocket)
        return self
```

### 📶 NATS Integration Patterns

::: info NATS Integration
NATS serves as the message bus connecting the API to agents and other services. The API uses NATS for agent discovery, sending events to agents, and subscribing to responses. Topic managers handle the complex routing and naming conventions for different types of agent communication.
:::

#### 🤖 Agent Communication

```python
class AgentIntegrationService:
    @staticmethod
    async def send_to_agent(nc: NATS, agent_class: str, agent_id: str, message: str) -> dict:
        # Create topic manager for agent communication
        topic_manager = AgentThreadTopicManager(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=str(ObjectId()),
            display_id=str(ObjectId()),
            run_id="*"  # Wildcard to match any run
        )
        
        # Create external event to send to agent
        external_event = ExternalAgentEvent(
            thread_id=topic_manager.thread_id,
            display_id=topic_manager.display_id,
            event=UserMessageEvent(messages=[ChatMessage(content=message, role=MessageRole.USER)])
        )
        
        # Send via NATS and wait for response
        response = await process_agent_response(nc, external_event, topic_manager)
        return {"response": response}
    
    @staticmethod
    async def discover_agents(nc: NATS) -> list[AgentDTO]:
        """Broadcast discovery request and collect responses."""
        # Uses NATS pub/sub pattern for agent discovery
        # Implementation details in AgentService
        return await AgentService.discover_agents(nc, locale_handler)
```

### 🧪 Testing Patterns

#### 🎮 Controller Testing

::: info Controller Testing Focus
Controller tests focus on HTTP-level concerns: request/response handling, authentication, authorization, and proper error status codes. These tests use the full FastAPI test client to simulate real HTTP requests and verify the complete request flow from endpoint to response.
:::

```python
@pytest.mark.asyncio
async def test_controller_endpoint(client: AsyncClient):
    # Test successful request with proper response structure
    response = await client.get("/resource/123")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == "123"
    
    # Test error handling with proper HTTP status codes
    response = await client.get("/resource/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    
    # Test authentication and authorization
    response = await client.get("/resource/123", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    
    # Test permission-based access control
    response = await client.get("/admin/resource/123")
    assert response.status_code == 403  # User lacks admin permission
```

#### 💼 Service Testing

::: info Service Testing Focus
Service tests focus on business logic, data processing, and integration with external systems like NATS and databases. These tests use mocks to isolate the service logic from external dependencies, allowing for fast, reliable unit testing of core functionality.
:::

```python
@pytest.mark.asyncio
async def test_service_logic():
    # Mock external dependencies to isolate business logic
    mock_nc = Mock()
    mock_locale = Mock()
    
    # Test core business logic without external dependencies
    result = await MyService.process_data(mock_nc, test_data, mock_locale)
    assert result.processed_field == "expected_value"
    assert result.status == "processed"
    
    # Test error handling in service layer
    with pytest.raises(HTTPException) as exc_info:
        await MyService.process_invalid_data(mock_nc, invalid_data, mock_locale)
    assert exc_info.value.status_code == 400
    assert "invalid data" in exc_info.value.detail.lower()
    
    # Test service interactions with mocked dependencies
    mock_nc.publish.assert_called_once()
    mock_locale.get_string.assert_called_with("success_message")
```


---
name: scaffold-api-endpoint
description: Generate a new REST API endpoint following the Controller-Service-DTO
  pattern. Creates the controller with fluent API, service with static methods,
  DTOs, and test setup.
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New REST API Endpoint

Generate boilerplate for a new API endpoint. The resource name/purpose should be provided via `$ARGUMENTS`.

## Before You Start

Read the API scope guide: `/home/user/aihub-core/aihub_api/AGENTS.md`

Study an existing controller for reference (check `aihub_api/aihub_api/routes/`).

## What to Generate

### 1. File Structure

Create in `aihub_api/aihub_api/`:

```
routes/<resource_name>/
├── __init__.py
├── controller.py     # FastAPI router with fluent API
├── service.py        # Business logic (static methods)
└── dto.py           # Request/Response Pydantic models
```

### 2. Controller (`controller.py`)

Follow the **fluent Controller pattern**:

- Create a class with `router = APIRouter(prefix="/<resource>", tags=["<Resource>"])`
- Methods return `Self` for chaining
- Use `Annotated` for dependency injection
- Use `Security(self.user_with_permission(...))` for auth
- Register routes in `__init__` with `router.add_api_route`

Key conventions:
- GET `/<resource>` — list resources
- GET `/<resource>/{id}` — get single resource
- POST `/<resource>` — create resource
- PUT `/<resource>/{id}` — update resource
- DELETE `/<resource>/{id}` — delete resource

### 3. Service (`service.py`)

- All methods are `@staticmethod` and async
- Decorated with `@trace_fn` for OpenTelemetry tracing
- Business logic separated from HTTP concerns
- Returns domain objects or raises exceptions

### 4. DTOs (`dto.py`)

- Pydantic `BaseModel` subclasses
- `<Resource>Request` — for POST/PUT body validation
- `<Resource>Response` — for response serialization
- Use modern type syntax: `str | None`, `list[str]`

### 5. Route Registration

Register the new router in the main app (typically `aihub_api/aihub_api/app.py` or a routes `__init__.py`).

### 6. i18n

Add translation keys for the new resource in all 4 locale files:
- `aihub_web/aihub_web/i18n/locales/{de,en,fr,it}.yaml`

### 7. Tests

Create in `aihub_api/tests/routes/<resource_name>/`:
- `test_<resource_name>.py` — Endpoint tests using ApiTestRunner

## Key Patterns

- **Controller → Service → Entity**: Strict separation of concerns
- **Fluent API**: Controller methods return `Self`
- **Dependency injection**: `Annotated[..., Depends(...)]` and `Security(...)`
- **Pydantic DTOs**: Never return raw dicts from endpoints
- **Async consistently**: All I/O operations use async/await
- **OpenTelemetry**: `@trace_fn` on all service methods

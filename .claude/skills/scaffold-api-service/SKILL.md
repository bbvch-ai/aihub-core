---
name: scaffold-api-service
description: Generate a new API service layer with stateless static methods, OpenTelemetry
  tracing, DTO conversion, pagination, and error handling. Follows the exact
  AgentService/ThreadService patterns.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob
---

# Scaffold a New API Service

Generate a service layer for a resource. The resource name should be provided via `$ARGUMENTS`.

## Before You Start

Read the API scope guide: `/home/user/aihub-core/aihub_api/AGENTS.md`

Study these reference services:
- CRUD: `aihub_api/aihub_api/routes/agent/AgentService.py`
- Pagination: `aihub_api/aihub_api/routes/thread/ThreadService.py`
- Bulk ops: `aihub_api/aihub_api/routes/notification/NotificationService.py`
- Simple: `aihub_api/aihub_api/routes/user/UserService.py`

## Architecture: Where Services Fit

```
Controller (HTTP layer)
    |
    v
Service (business logic)    <-- YOU ARE HERE
    |
    v
Entity (MongoEngine Document = schema + repository)
    |
    v
MongoDB (via FerretDB)
```

Services are the **business logic layer**. They:
- Accept primitive types and DTOs as parameters
- Call Entity class methods for data access
- Return DTOs to controllers
- Raise `HTTPException` for errors
- Are stateless (all methods are `@staticmethod`)

## Step 1: Create the Service

File: `aihub_api/aihub_api/routes/<resource>/<Resource>Service.py`

```python
from fastapi import HTTPException
from mongoengine import DoesNotExist, NotUniqueError

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.<resource>.<Resource>Entity import <Resource>Entity

from aihub_api.routes.<resource>.dto.Create<Resource>Request import Create<Resource>Request
from aihub_api.routes.<resource>.dto.<Resource>DTO import <Resource>DTO
from aihub_api.routes.<resource>.dto.Update<Resource>Request import Update<Resource>Request


class <Resource>Service:
    """Business logic for <resource> operations."""

    # ==================== READ ====================

    @staticmethod
    @trace_fn
    async def get_<resource>_by_id(<resource>_id: str, t: LocaleHandler) -> <Resource>DTO:
        """Retrieve a single <resource> by ID."""
        try:
            entity = <Resource>Entity.get_by_id(<resource>_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="<Resource> not found.")
        return <Resource>DTO.from_entity(entity, t)

    @staticmethod
    @trace_fn
    async def get_paginated_<resource>s(
        user_id: str,
        t: LocaleHandler,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[<Resource>DTO]]:
        """Retrieve a paginated list of <resource>s for a user."""
        skip = (page - 1) * page_size
        total = <Resource>Entity.count_for_user(user_id)
        entities = <Resource>Entity.get_paginated_for_user(
            user_id, skip=skip, limit=page_size,
        )
        dtos = [<Resource>DTO.from_entity(entity, t) for entity in entities]
        return total, dtos

    # ==================== CREATE ====================

    @staticmethod
    @trace_fn
    async def create_<resource>(
        request: Create<Resource>Request,
        user: UserIdentity,
        t: LocaleHandler,
    ) -> <Resource>DTO:
        """Create a new <resource>."""
        try:
            entity = <Resource>Entity.create_<resource>(
                name=request.name,
                user_id=user.id,
                # ... map request fields to entity fields
            )
        except NotUniqueError:
            raise HTTPException(status_code=409, detail="<Resource> with this name already exists.")
        return <Resource>DTO.from_entity(entity, t)

    # ==================== UPDATE ====================

    @staticmethod
    @trace_fn
    async def update_<resource>(
        <resource>_id: str,
        request: Update<Resource>Request,
        t: LocaleHandler,
    ) -> <Resource>DTO:
        """Update an existing <resource>."""
        try:
            entity = <Resource>Entity.get_by_id(<resource>_id)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="<Resource> not found.")

        # Apply only provided fields (partial update)
        if request.name is not None:
            entity.name = request.name
        if request.description is not None:
            entity.description = request.description

        entity.save()
        return <Resource>DTO.from_entity(entity, t)

    # ==================== DELETE ====================

    @staticmethod
    @trace_fn
    async def delete_<resource>(<resource>_id: str) -> None:
        """Delete a <resource>."""
        try:
            entity = <Resource>Entity.get_by_id(<resource>_id)
            entity.delete()
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="<Resource> not found.")
```

## Service Patterns Reference

### Pattern 1: Simple CRUD

```python
@staticmethod
@trace_fn
async def get_resource(resource_id: str, t: LocaleHandler) -> ResourceDTO:
    entity = ResourceEntity.get_by_id(resource_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Not found")
    return ResourceDTO.from_entity(entity, t)
```

### Pattern 2: Pagination with Filtering

```python
@staticmethod
@trace_fn
async def get_paginated_resources(
    user_id: str,
    t: LocaleHandler,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
) -> tuple[int, list[ResourceDTO]]:
    skip = (page - 1) * page_size
    total, entities = ResourceEntity.get_with_filters(
        user_id=user_id, skip=skip, limit=page_size, status=status_filter,
    )
    dtos = [ResourceDTO.from_entity(e, t) for e in entities]
    return total, dtos
```

### Pattern 3: Create with Validation

```python
@staticmethod
@trace_fn
async def create_resource(request: CreateRequest, user: UserIdentity, t: LocaleHandler) -> ResourceDTO:
    # Validate business rules
    existing = ResourceEntity.find_by_name(request.name)
    if existing:
        raise HTTPException(status_code=409, detail="Already exists")

    # Create entity
    entity = ResourceEntity(
        name=request.name,
        user_id=user.id,
        config_data=request.configuration,
    )
    entity.save()
    return ResourceDTO.from_entity(entity, t)
```

### Pattern 4: Complex Aggregation

```python
@staticmethod
@trace_fn
async def get_resource_with_stats(resource_id: str, t: LocaleHandler) -> ResourceWithStatsDTO:
    entity = ResourceEntity.get_by_id(resource_id)
    # MongoDB aggregation for statistics
    stats = EventEntity.get_aggregated_statistics(resource_id)
    return ResourceWithStatsDTO.from_entity_and_stats(entity, stats, t)
```

### Pattern 5: Parallel Fetching

```python
@staticmethod
@trace_fn
async def get_resource_detail(resource_id: str, t: LocaleHandler) -> DetailDTO:
    # Fetch multiple related entities in parallel
    entity, related_items, stats = await asyncio.gather(
        ResourceEntity.async_get_by_id(resource_id),
        RelatedEntity.async_get_for_resource(resource_id),
        StatsEntity.async_get_for_resource(resource_id),
    )
    return DetailDTO.from_entities(entity, related_items, stats, t)
```

### Pattern 6: Caching Expensive Lookups

```python
from cachetools import TTLCache, cached

@staticmethod
@cached(TTLCache(maxsize=128, ttl=60))
def _fetch_cached_resource(resource_id: str, t: LocaleHandler) -> ResourceDTO | None:
    """Cached lookup to avoid repeated DB queries."""
    try:
        entity = ResourceEntity.get_by_id(resource_id)
        return ResourceDTO.from_entity(entity, t)
    except DoesNotExist:
        return None
```

## Step 2: Create DTOs

### Response DTO

File: `aihub_api/aihub_api/routes/<resource>/dto/<Resource>DTO.py`

```python
from typing import Annotated, Self
from datetime import datetime

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.<resource>.<Resource>Entity import <Resource>Entity


class <Resource>DTO(BaseModel):
    """Response DTO for <resource> data."""

    id: Annotated[str, Field(description="Unique <resource> ID")]
    name: Annotated[str, Field(description="<Resource> name")]
    description: Annotated[str | None, Field(description="<Resource> description")] = None
    status: Annotated[str, Field(description="Current status")]
    created_at: Annotated[datetime, Field(description="Creation timestamp")]

    @classmethod
    def from_entity(cls, entity: <Resource>Entity, t: LocaleHandler) -> Self:
        """Convert a MongoEngine entity to a DTO."""
        return cls(
            id=str(entity.id),
            name=t.extract(entity.name.to_locale_string()) if entity.name else "",
            description=t.extract(entity.description.to_locale_string()) if entity.description else None,
            status=entity.status,
            created_at=entity.created_at,
        )
```

### Request DTOs

File: `aihub_api/aihub_api/routes/<resource>/dto/Create<Resource>Request.py`

```python
from typing import Annotated
from pydantic import BaseModel, Field


class Create<Resource>Request(BaseModel):
    """Request body for creating a <resource>."""

    name: Annotated[str, Field(min_length=1, max_length=200, description="<Resource> name")]
    description: Annotated[str | None, Field(max_length=2000, description="Optional description")] = None
```

File: `aihub_api/aihub_api/routes/<resource>/dto/Update<Resource>Request.py`

```python
from typing import Annotated
from pydantic import BaseModel, Field


class Update<Resource>Request(BaseModel):
    """Request body for updating a <resource>. All fields optional."""

    name: Annotated[str | None, Field(min_length=1, max_length=200, description="New name")] = None
    description: Annotated[str | None, Field(max_length=2000, description="New description")] = None
    status: Annotated[str | None, Field(pattern=r"^(active|inactive|archived)$", description="New status")] = None
```

### Paginated Response

File: `aihub_api/aihub_api/routes/<resource>/dto/Paginated<Resource>sResponse.py`

```python
from typing import Annotated
from pydantic import Field

from aihub_api.pagination.PageDTO import PageDTO
from aihub_api.routes.<resource>.dto.<Resource>DTO import <Resource>DTO


class Paginated<Resource>sResponse(PageDTO):
    """Paginated response containing a list of <resource>s."""

    <resource>s: Annotated[list[<Resource>DTO], Field(description="List of <resource>s for the current page")]
```

### DTO Conventions

| Pattern | Naming | Purpose |
|---------|--------|---------|
| Response | `<Resource>DTO` | Standard response |
| Full response | `Full<Resource>DTO` | Detailed response with relations |
| Minimal response | `Minimal<Resource>DTO` | Lightweight list item |
| Create request | `Create<Resource>Request` | POST body |
| Update request | `Update<Resource>Request` | PUT/PATCH body (all fields optional) |
| Paginated response | `Paginated<Resource>sResponse` | Extends `PageDTO` |

### DTO Rules

1. **All fields use `Annotated[Type, Field(...)]`** with descriptions
2. **`from_entity` classmethod** for Entity-to-DTO conversion
3. **Locale handling**: Use `t.extract(entity.name.to_locale_string())` for i18n fields
4. **Modern syntax**: `str | None` not `Optional[str]`
5. **Validation in requests**: `Field(min_length=1, max_length=200, pattern=...)`
6. **Inheritance for paginated**: Extend `PageDTO` (provides total, page, page_size, total_pages)

## Key Conventions

- **All methods `@staticmethod`**: Services are stateless
- **All methods `@trace_fn`**: OpenTelemetry tracing
- **All methods `async`**: Even if currently sync (future-proofing)
- **Raise `HTTPException`**: For all error cases (404, 409, 400)
- **Return DTOs**: Never return raw entities or dicts
- **Accept `LocaleHandler`**: For i18n string extraction
- **`DoesNotExist` / `NotUniqueError`**: MongoEngine exceptions to catch
- **No defensive try-catch**: Let unexpected errors propagate

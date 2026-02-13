---
name: scaffold-api-endpoint
description: Generate a new REST API controller with fluent builder pattern, typed
  endpoints, permission-based auth, DTOs, and main.py registration. Use when user says
  "create API endpoint", "scaffold controller", "new REST endpoint", "add CRUD API",
  "generate API route", "build endpoint for X", or "add API controller".
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Scaffold a New REST API Controller

Generate a new controller with endpoints. The resource name should be provided via `$ARGUMENTS`.

## Step 1: Read Reference Materials

1. Read the API scope guide: `/home/user/aihub-core/aihub_api/AGENTS.md`
2. Study these reference controllers:
   - CRUD: `aihub_api/aihub_api/routes/agent/AgentController.py`
   - Simple: `aihub_api/aihub_api/routes/role/RoleController.py`
   - Complex: `aihub_api/aihub_api/routes/thread/ThreadController.py`
   - Base class: `aihub_lib/aihub_lib/routes/Controller.py`
   - Registration: `aihub_api/app/main.py`
3. Extract the resource name from `$ARGUMENTS` and derive `snake_case` (dirs/files) and `CamelCase` (classes)

## Step 2: Create Directory Structure

```
aihub_api/aihub_api/routes/<resource>/
├── __init__.py
├── <Resource>Controller.py
├── <Resource>Service.py
└── dto/
    ├── __init__.py
    ├── <Resource>DTO.py
    ├── Create<Resource>Request.py
    ├── Update<Resource>Request.py
    └── Paginated<Resource>sResponse.py
```

## Step 3: Create the Controller

File: `aihub_api/aihub_api/routes/<resource>/<Resource>Controller.py`

```python
from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Response, Security, status

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.<resource>.dto.Create<Resource>Request import Create<Resource>Request
from aihub_api.routes.<resource>.dto.<Resource>DTO import <Resource>DTO
from aihub_api.routes.<resource>.dto.Paginated<Resource>sResponse import Paginated<Resource>sResponse
from aihub_api.routes.<resource>.dto.Update<Resource>Request import Update<Resource>Request
from aihub_api.routes.<resource>.<Resource>Service import <Resource>Service


class <Resource>Controller(Controller):
    """Controller for <resource> management."""

    name = ApiLocaleString.from_i18n_path("api.controllers.<resource>.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.<resource>.description")
    icon = "mage:icon-name"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/<resource>s",
        additionally_required_permission: str | None = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    # ==================== LIST ====================

    def get_<resource>s(self, route: str = "/") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_<resource>s(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> Paginated<Resource>sResponse:
            """Retrieve a paginated list of <resource>s."""
            total, items = await <Resource>Service.get_paginated_<resource>s(
                user_id=user.id, t=t, page=page, page_size=page_size,
            )
            total_pages = (total + page_size - 1) // page_size
            return Paginated<Resource>sResponse(
                <resource>s=items, total=total, page=page,
                page_size=page_size, total_pages=total_pages,
            )
        return self

    # ==================== GET ====================

    def get_<resource>(self, route: str = "/{<resource>_id}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_<resource>(
            <resource>_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.<resource>.{<resource>_id}"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> <Resource>DTO:
            """Retrieve details for a specific <resource>."""
            return await <Resource>Service.get_<resource>_by_id(<resource>_id, t)
        return self

    # ==================== CREATE ====================

    def create_<resource>(self, route: str = "/") -> Self:
        @self.router.post(route, tags=self.tags, status_code=status.HTTP_201_CREATED)
        async def create_<resource>(
            request: Create<Resource>Request,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.<resource>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> <Resource>DTO:
            """Create a new <resource>."""
            return await <Resource>Service.create_<resource>(request, user, t)
        return self

    # ==================== UPDATE ====================

    def update_<resource>(self, route: str = "/{<resource>_id}") -> Self:
        @self.router.put(route, tags=self.tags)
        async def update_<resource>(
            <resource>_id: str,
            request: Update<Resource>Request,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.<resource>.{<resource>_id}"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> <Resource>DTO:
            """Update an existing <resource>."""
            return await <Resource>Service.update_<resource>(<resource>_id, request, t)
        return self

    # ==================== DELETE ====================

    def delete_<resource>(self, route: str = "/{<resource>_id}") -> Self:
        @self.router.delete(route, tags=self.tags, status_code=status.HTTP_204_NO_CONTENT)
        async def delete_<resource>(
            <resource>_id: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.<resource>.{<resource>_id}"))],
        ) -> Response:
            """Delete a <resource>."""
            await <Resource>Service.delete_<resource>(<resource>_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        return self
```

### Controller Architecture Rules

1. **Inherit from `Controller`**: Always extend `aihub_lib.routes.Controller`
2. **Fluent builder**: Every endpoint method returns `Self` for chaining
3. **Metadata**: Set `name` (ApiLocaleString), `description`, `icon` (Iconify)
4. **Named-only constructor args**: Use `*` to enforce keyword arguments
5. **Default route**: Set in constructor `route: str = "/<resource>s"`
6. **Inner function pattern**: Endpoint function is defined inside the method
7. **Permission templates**: Use `{path_param}` placeholders for dynamic permission checks
8. **Tags**: Always pass `tags=self.tags` to router decorators
9. **Status codes**: 201 for create, 204 for delete, 200 (default) for get/update

### Permission Patterns

| Access Level | Template | Usage |
|-------------|----------|-------|
| Any user | `"aihub.user.?>"` | List own resources |
| Specific resource | `"aihub.user.<resource>.{<resource>_id}"` | View specific resource |
| Admin-only | `"aihub.admin.<resource>"` | Create resources |
| Admin + resource | `"aihub.admin.<resource>.{<resource>_id}"` | Update/delete |
| Service admin | `f"aihub.admin.service.{self.service_name}"` | Manage entire service |

### User Identity Usage

```python
# When you need the identity (e.g., filter by user):
user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))]
# Access: user.id, user.name, user.email, user.roles

# When you only need permission check:
_: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.<resource>"))]
```

## Step 4: Register in main.py

Edit `aihub_api/app/main.py`:

```python
from aihub_api.routes.<resource>.<Resource>Controller import <Resource>Controller

runner.mount(
    # ... existing controllers ...
    <Resource>Controller(auth=auth)
        .get_<resource>s()
        .get_<resource>()
        .create_<resource>()
        .update_<resource>()
        .delete_<resource>(),
)
```

## Step 5: Add i18n Keys

Add to `aihub_api/aihub_api/i18n/locales/{en,de,fr,it}.yaml`:

```yaml
api:
  controllers:
    <resource>:
      name: "<Resource>s"
      description: "Manage <resource>s"
```

## Key Conventions

- **Controller is thin**: Delegates to Service, only handles HTTP concerns
- **`Annotated` for everything**: Params, dependencies, auth — all use `Annotated`
- **Docstrings on endpoints**: Short description of what the endpoint does
- **Locale handler**: Always inject `t: Annotated[LocaleHandler, Depends(use_locale)]`
- **Pagination types**: Use `PageNumber` and `PageSize` type aliases from `aihub_api.pagination.type`
- **Error handling**: Let services raise `HTTPException` -- don't catch in controllers
- **Path validation**: Use `Path(pattern=r"^[a-f0-9]{24}$")` for MongoDB ObjectId params

## Examples

**Input**: `$ARGUMENTS = "project"`
**Expected output files**:
- `aihub_api/aihub_api/routes/project/ProjectController.py` with `ProjectController(Controller)`
- `aihub_api/aihub_api/routes/project/ProjectService.py` (stub -- use `/scaffold-api-service` for full service)
- `aihub_api/aihub_api/routes/project/dto/ProjectDTO.py`, `CreateProjectRequest.py`, `UpdateProjectRequest.py`, `PaginatedProjectsResponse.py`
- Registration added to `aihub_api/app/main.py`
- i18n keys added to `aihub_api/aihub_api/i18n/locales/{en,de,fr,it}.yaml`

## Troubleshooting

- **404 on new endpoint**: Verify the controller is mounted in `main.py` and the fluent builder methods are chained
- **Permission denied (403)**: Check the permission template string matches what is configured in the role system (e.g., `aihub.user.?>` vs `aihub.admin.resource`)
- **Missing tags in Swagger**: Ensure `tags=self.tags` is passed to every router decorator
- **i18n key not found**: Verify locale YAML files have the correct nested path under `api.controllers.<resource>`
- **Duplicate route conflict**: Check that `route` parameter default values do not clash with existing controllers

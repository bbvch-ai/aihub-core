from typing import Annotated, Self

from fastapi import Depends, Path, Query, Security
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.memory.dto.delete_memory_response import DeleteAllMemoriesResponse, DeleteMemoryResponse
from swiss_ai_hub.api.routes.memory.dto.memories_response import MemoriesResponse
from swiss_ai_hub.api.routes.memory.dto.memory_search_response import MemorySearchResponse
from swiss_ai_hub.api.routes.memory.dto.update_memory_request import UpdateMemoryRequest
from swiss_ai_hub.api.routes.memory.dto.update_memory_response import UpdateMemoryResponse
from swiss_ai_hub.api.routes.memory.organization_memory_service import OrganizationMemoryService


class OrganizationMemoryController(TenantScopedController):
    """Controller for managing organization/tenant memories."""

    name = ApiLocaleString.from_i18n_path("api.controllers.organization_memory.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.organization_memory.description")
    icon = "mdi:domain"

    def __init__(self, *, auth: AuthHandler, route: str = "/organization-memories", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    def get_organization_memories(self, route: str = "") -> Self:
        @self.router.get(route, tags=self.tags, response_model=MemoriesResponse)
        async def get_organization_memories(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.organization"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            limit: Annotated[int, Query(ge=1, le=1000, description="Maximum number of memories to return")] = 100,
        ) -> MemoriesResponse:
            return await OrganizationMemoryService.get_memories(
                limit=limit,
                t=t,
            )

        return self

    def search_organization_memories(self, route: str = "/search") -> Self:
        @self.router.get(route, tags=self.tags, response_model=MemorySearchResponse)
        async def search_organization_memories(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.organization"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            query: Annotated[str, Query(description="Search query for semantic search")],
            limit: Annotated[int, Query(ge=1, le=1000, description="Maximum number of results to return")] = 100,
            agent_class: Annotated[str | None, Query(description="Filter by agent class")] = None,
            agent_id: Annotated[str | None, Query(description="Filter by agent ID")] = None,
            thread_id: Annotated[str | None, Query(description="Filter by thread ID")] = None,
        ) -> MemorySearchResponse:
            return await OrganizationMemoryService.search_memories(
                query=query,
                limit=limit,
                agent_class=agent_class,
                agent_id=agent_id,
                thread_id=thread_id,
                t=t,
            )

        return self

    def delete_organization_memory(self, route: str = "/{memory_id}") -> Self:
        @self.router.delete(route, tags=self.tags, response_model=DeleteMemoryResponse)
        async def delete_organization_memory(
            memory_id: Annotated[str, Path(description="Memory ID to delete")],
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.organization"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> DeleteMemoryResponse:
            return await OrganizationMemoryService.delete_memory(
                memory_id=memory_id,
                t=t,
            )

        return self

    def delete_all_organization_memories(self, route: str = "") -> Self:
        @self.router.delete(route, tags=self.tags, response_model=DeleteAllMemoriesResponse)
        async def delete_all_organization_memories(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.organization"))],
            # Required because OrganizationMemory.__init__ needs LocaleHandler for Mem0Service i18n graph prompts
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> DeleteAllMemoriesResponse:
            return await OrganizationMemoryService.delete_all_memories(
                t=t,
            )

        return self

    def update_organization_memory(self, route: str = "/{memory_id}") -> Self:
        @self.router.patch(route, tags=self.tags, response_model=UpdateMemoryResponse)
        async def update_organization_memory(
            memory_id: Annotated[str, Path(description="Memory ID to update")],
            request: UpdateMemoryRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.organization"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> UpdateMemoryResponse:
            return await OrganizationMemoryService.update_memory(
                memory_id=memory_id,
                data=request.data,
                t=t,
            )

        return self

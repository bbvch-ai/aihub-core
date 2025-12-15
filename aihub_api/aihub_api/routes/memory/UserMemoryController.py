from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Path, Query, Security

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.memory.dto.DeleteMemoryResponse import DeleteAllMemoriesResponse, DeleteMemoryResponse
from aihub_api.routes.memory.dto.MemoriesResponse import MemoriesResponse
from aihub_api.routes.memory.dto.MemorySearchResponse import MemorySearchResponse
from aihub_api.routes.memory.dto.UpdateMemoryRequest import UpdateMemoryRequest
from aihub_api.routes.memory.dto.UpdateMemoryResponse import UpdateMemoryResponse
from aihub_api.routes.memory.UserMemoryService import UserMemoryService


class UserMemoryController(Controller):
    """Controller for managing user memories."""

    name = LocaleString(en="User Memories")
    description = LocaleString(en="View and manage your personal memories from mem0")
    icon = "mdi:account-brain"

    def __init__(self, *, auth: AuthHandler, route: str = "/user-memories", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    def get_user_memories(self, route: str = "") -> "UserMemoryController":
        @self.router.get(route, tags=self.tags, response_model=MemoriesResponse)
        async def get_user_memories(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.user"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            limit: Annotated[int, Query(ge=1, le=1000, description="Maximum number of memories to return")] = 100,
        ) -> MemoriesResponse:
            return await UserMemoryService.get_memories_for_user(
                user=user,
                limit=limit,
                t=t,
            )

        return self

    def search_user_memories(self, route: str = "/search") -> "UserMemoryController":
        @self.router.get(route, tags=self.tags, response_model=MemorySearchResponse)
        async def search_user_memories(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.user"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            query: Annotated[str, Query(description="Search query for semantic search")],
            limit: Annotated[int, Query(ge=1, le=1000, description="Maximum number of results to return")] = 100,
            agent_id: Annotated[str | None, Query(description="Filter by agent ID")] = None,
            thread_id: Annotated[str | None, Query(description="Filter by thread ID")] = None,
        ) -> MemorySearchResponse:
            return await UserMemoryService.search_memories(
                user=user,
                query=query,
                limit=limit,
                agent_id=agent_id,
                thread_id=thread_id,
                t=t,
            )

        return self

    def delete_user_memory(self, route: str = "/{memory_id}") -> "UserMemoryController":
        @self.router.delete(route, tags=self.tags, response_model=DeleteMemoryResponse)
        async def delete_user_memory(
            memory_id: Annotated[str, Path(description="Memory ID to delete")],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.user"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> DeleteMemoryResponse:
            return await UserMemoryService.delete_memory(user=user, memory_id=memory_id, t=t)

        return self

    def delete_all_user_memories(self, route: str = "") -> "UserMemoryController":
        @self.router.delete(route, tags=self.tags, response_model=DeleteAllMemoriesResponse)
        async def delete_all_user_memories(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.user"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> DeleteAllMemoriesResponse:
            return await UserMemoryService.delete_all_memories(
                user=user,
                t=t,
            )

        return self

    def update_user_memory(self, route: str = "/{memory_id}") -> "UserMemoryController":
        @self.router.patch(route, tags=self.tags, response_model=UpdateMemoryResponse)
        async def update_user_memory(
            memory_id: Annotated[str, Path(description="Memory ID to update")],
            request: UpdateMemoryRequest,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.memory.user"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> UpdateMemoryResponse:
            return await UserMemoryService.update_memory(user=user, memory_id=memory_id, data=request.data, t=t)

        return self

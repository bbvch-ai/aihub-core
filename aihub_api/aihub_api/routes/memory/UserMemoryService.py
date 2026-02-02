from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.memory.UserMemory import UserMemory
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

from aihub_api.routes.memory.dto.DeleteMemoryResponse import DeleteAllMemoriesResponse, DeleteMemoryResponse
from aihub_api.routes.memory.dto.MemoriesResponse import MemoriesResponse
from aihub_api.routes.memory.dto.MemoryDTO import MemoryDTO
from aihub_api.routes.memory.dto.MemoryRelationDTO import MemoryRelationDTO
from aihub_api.routes.memory.dto.MemorySearchResponse import MemorySearchResponse
from aihub_api.routes.memory.dto.UpdateMemoryResponse import UpdateMemoryResponse


class UserMemoryService:
    """Service layer for user memory operations."""

    @staticmethod
    @trace_fn
    async def get_memories_for_user(
        user: UserIdentity,
        limit: int,
        t: LocaleHandler,
    ) -> MemoriesResponse:
        user_memory = UserMemory(user=user, t=t)
        all_result = await user_memory.get_all()

        memories = all_result.results

        limited_memories = memories[:limit]
        memory_dtos = [MemoryDTO.from_memory(m) for m in limited_memories]
        relation_dtos = [MemoryRelationDTO.from_relation(r) for r in all_result.relations]

        return MemoriesResponse(
            total=len(limited_memories),
            memories=memory_dtos,
            relations=relation_dtos,
        )

    @staticmethod
    @trace_fn
    async def search_memories(
        user: UserIdentity,
        query: str,
        limit: int,
        agent_id: str | None,
        thread_id: str | None,
        t: LocaleHandler,
    ) -> MemorySearchResponse:
        user_memory = UserMemory(user=user, t=t)
        search_result = await user_memory.search_user_memory(
            query=query,
            agent_id=agent_id,
            thread_id=thread_id,
            limit=limit,
        )

        memory_dtos = [MemoryDTO.from_memory(m) for m in search_result.results]
        relation_dtos = [MemoryRelationDTO.from_relation(r) for r in search_result.relations]

        return MemorySearchResponse(
            query=query,
            total=len(memory_dtos),
            memories=memory_dtos,
            relations=relation_dtos,
        )

    @staticmethod
    @trace_fn
    async def delete_memory(user: UserIdentity, memory_id: str, t: LocaleHandler) -> DeleteMemoryResponse:
        user_memory = UserMemory(user=user, t=t)
        await user_memory.delete_memory(memory_id=memory_id)
        return DeleteMemoryResponse(status="deleted", memory_id=memory_id)

    @staticmethod
    @trace_fn
    async def delete_all_memories(
        user: UserIdentity,
        t: LocaleHandler,
    ) -> DeleteAllMemoriesResponse:
        user_memory = UserMemory(user=user, t=t)
        await user_memory.delete_all()
        return DeleteAllMemoriesResponse(status="deleted")

    @staticmethod
    @trace_fn
    async def update_memory(user: UserIdentity, memory_id: str, data: str, t: LocaleHandler) -> UpdateMemoryResponse:
        user_memory = UserMemory(user=user, t=t)
        await user_memory.update_memory(memory_id=memory_id, data=data)
        return UpdateMemoryResponse(status="updated", memory_id=memory_id)

from aihub_lib.generative_ai.memory.OrganizationMemory import OrganizationMemory
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

from aihub_api.routes.memory.dto.DeleteMemoryResponse import DeleteAllMemoriesResponse, DeleteMemoryResponse
from aihub_api.routes.memory.dto.MemoriesResponse import MemoriesResponse
from aihub_api.routes.memory.dto.MemoryDTO import MemoryDTO
from aihub_api.routes.memory.dto.MemoryRelationDTO import MemoryRelationDTO
from aihub_api.routes.memory.dto.MemorySearchResponse import MemorySearchResponse
from aihub_api.routes.memory.dto.UpdateMemoryResponse import UpdateMemoryResponse


class OrganizationMemoryService:
    """Service layer for organization/tenant memory operations."""

    @staticmethod
    @trace_fn
    async def get_memories(
        limit: int,
        t: LocaleHandler,
    ) -> MemoriesResponse:
        org_memory = OrganizationMemory(t=t)
        all_result = await org_memory.get_all()

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
        query: str,
        limit: int,
        agent_class: str | None,
        agent_id: str | None,
        thread_id: str | None,
        t: LocaleHandler,
    ) -> MemorySearchResponse:
        # Combine agent_class and agent_id into mem0 format: "agent_class/agent_id"
        # This matches how AgentMemory stores agent_id (see AgentMemory.agent_id property)
        combined_agent_id = None
        if agent_class and agent_id:
            combined_agent_id = f"{agent_class}/{agent_id}"

        org_memory = OrganizationMemory(t=t)
        search_result = await org_memory.search_organization_memory(
            query=query,
            agent_id=combined_agent_id,
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
    async def delete_memory(
        memory_id: str,
        t: LocaleHandler,
    ) -> DeleteMemoryResponse:
        org_memory = OrganizationMemory(t=t)
        await org_memory.delete_memory(memory_id=memory_id)
        return DeleteMemoryResponse(status="deleted", memory_id=memory_id)

    @staticmethod
    @trace_fn
    async def delete_all_memories(
        t: LocaleHandler,
    ) -> DeleteAllMemoriesResponse:
        org_memory = OrganizationMemory(t=t)
        await org_memory.delete_all()
        return DeleteAllMemoriesResponse(status="deleted")

    @staticmethod
    @trace_fn
    async def update_memory(
        memory_id: str,
        data: str,
        t: LocaleHandler,
    ) -> UpdateMemoryResponse:
        org_memory = OrganizationMemory(t=t)
        await org_memory.update_memory(memory_id=memory_id, data=data)
        return UpdateMemoryResponse(status="updated", memory_id=memory_id)

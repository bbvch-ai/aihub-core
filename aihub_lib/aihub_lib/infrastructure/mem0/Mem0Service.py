from mem0.configs.base import MemoryConfig

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.graph.PatchedMemoryGraph import PatchedMemoryGraph
from aihub_lib.infrastructure.mem0.PatchedAsyncMemory import PatchedAsyncMemory
from aihub_lib.infrastructure.mem0.types.Memory import Memory
from aihub_lib.infrastructure.mem0.types.MemoryAdded import MemoryAdded
from aihub_lib.infrastructure.mem0.types.MemorySearchResult import MemorySearchResult
from aihub_lib.infrastructure.mem0.types.MemoryType import MemoryType


class Mem0Service:
    def __init__(
        self,
        config: MemoryConfig,
        t: LocaleHandler,
    ):
        self._config = config
        self._memory = PatchedAsyncMemory(config=config)
        self._memory.graph = PatchedMemoryGraph.from_graph(self._memory.graph, t=t)

    @property
    def config(self):
        return self._config

    async def add_memory(
        self,
        messages: list[dict[str, str]],
        owner_id: str,
        memory_type: MemoryType,
        user_id: str,
        agent_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        organization_name: str | None = None,
        organization_namespace: str | None = None,
        infer: bool = True,
    ) -> MemoryAdded:
        metadata = {
            "_type": memory_type.value,
            "_user_id": user_id,
            "_agent_id": agent_id,
            "_thread_id": thread_id,
            "_display_id": display_id,
            "_run_id": run_id,
            "_organization_name": organization_name,
            "_organization_namespace": organization_namespace,
        }
        metadata = {k: str(v) for k, v in metadata.items() if v is not None}
        added_memory = await self._memory.add(
            messages,
            user_id=owner_id,
            metadata=metadata,
            infer=infer,
        )

        added_entities, deleted_entities = [], []
        for i, relation in enumerate(added_memory["relations"]["added_entities"]):
            if isinstance(relation, list):
                added_entities.extend(relation)
            else:
                added_entities.append(relation)
        for i, relation in enumerate(added_memory["relations"]["deleted_entities"]):
            if isinstance(relation, list):
                deleted_entities.extend(relation)
            else:
                deleted_entities.append(relation)

        added_memory["relations"]["added_entities"] = added_entities
        added_memory["relations"]["deleted_entities"] = deleted_entities

        return MemoryAdded.model_validate(
            {
                **added_memory,
                "owner_id": owner_id,
                "_user_id": user_id,
                "_agent_id": agent_id,
                "_thread_id": thread_id,
                "_display_id": display_id,
                "_run_id": run_id,
                "_organization_name": organization_name,
                "_organization_namespace": organization_namespace,
                "_type": memory_type.value,
            }
        )

    async def get_memory(self, memory_id: str) -> Memory:
        memory = await self._memory.get(memory_id)
        return Memory.model_validate(memory)

    async def delete_memory(self, memory_id: str):
        await self._memory.delete(memory_id)

    async def update_memory(self, memory_id: str, data: str):
        await self._memory.update(memory_id=memory_id, data=data)

    async def search(
        self,
        query: str,
        owner_id: str,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        memory_type: MemoryType | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        organization_name: str | None = None,
        organization_namespace: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        filters = {
            "_type": memory_type.value,
            "_user_id": user_id,
            "_agent_id": agent_id,
            "_thread_id": thread_id,
            "_display_id": display_id,
            "_run_id": run_id,
            "_organization_name": organization_name,
            "_organization_namespace": organization_namespace,
        }
        filters = {k: str(v) for k, v in filters.items() if v is not None}
        memories = await self._memory.search(
            query=query,
            user_id=owner_id,
            limit=limit,
            filters=filters,
            threshold=threshold,
            rerank=rerank,
        )
        return MemorySearchResult.model_validate(memories)

    async def delete_all(
        self,
        owner_id: str,
    ):
        await self._memory.delete_all(user_id=owner_id)

    async def get_all(
        self,
        owner_id: str,
    ) -> MemorySearchResult:
        memories = await self._memory.get_all(user_id=owner_id, limit=10_000)
        return MemorySearchResult.model_validate(memories)

from mem0.configs.base import MemoryConfig

from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.graph.patched_memory_graph import PatchedMemoryGraph
from swiss_ai_hub.core.infrastructure.mem0.patched_async_memory import PatchedAsyncMemory
from swiss_ai_hub.core.infrastructure.mem0.patched_milvus_db import PatchedMilvusDB
from swiss_ai_hub.core.infrastructure.mem0.patched_open_ai_embedding import PatchedOpenAIEmbedding
from swiss_ai_hub.core.infrastructure.mem0.patched_open_aillm import PatchedOpenAILLM
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_added import MemoryAdded
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType


class Mem0Service:
    def __init__(
        self,
        config: MemoryConfig,
        t: LocaleHandler,
    ):
        self._config = config
        self._memory = PatchedAsyncMemory(config=config)
        self._memory.vector_store = PatchedMilvusDB.from_milvus(self._memory.vector_store)
        self._memory.llm = PatchedOpenAILLM.from_llm(self._memory.llm)
        self._memory.embedding_model = PatchedOpenAIEmbedding.from_embedding(self._memory.embedding_model)
        # When the graph store is disabled, mem0 sets enable_graph=False and self.graph=None — nothing to wrap.
        if self._memory.enable_graph:
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
        tenant_id: str | None = None,
        tenant_namespace: str | None = None,
        infer: bool = True,
    ) -> MemoryAdded:
        metadata = {
            "_type": memory_type.value,
            "_user_id": user_id,
            "_agent_id": agent_id,
            "_thread_id": thread_id,
            "_display_id": display_id,
            "_run_id": run_id,
            "_tenant_id": tenant_id,
            "_tenant_namespace": tenant_namespace,
        }
        # Filter out None values and empty strings
        metadata = {k: str(v) for k, v in metadata.items() if v is not None and v != ""}
        added_memory = await self._memory.add(
            messages,
            user_id=owner_id,
            metadata=metadata,
            infer=infer,
        )

        # mem0 omits the "relations" key entirely when the graph store is disabled (main.py returns only
        # {"results": ...}); default to an empty structure so graph-off writes don't KeyError.
        relations = added_memory.get("relations") or {}
        added_entities, deleted_entities = [], []
        for relation in relations.get("added_entities", []):
            if isinstance(relation, list):
                added_entities.extend(relation)
            else:
                added_entities.append(relation)
        for relation in relations.get("deleted_entities", []):
            if isinstance(relation, list):
                deleted_entities.extend(relation)
            else:
                deleted_entities.append(relation)

        added_memory["relations"] = {"added_entities": added_entities, "deleted_entities": deleted_entities}

        return MemoryAdded.model_validate(
            {
                **added_memory,
                "owner_id": owner_id,
                "_user_id": user_id,
                "_agent_id": agent_id,
                "_thread_id": thread_id,
                "_display_id": display_id,
                "_run_id": run_id,
                "_tenant_id": tenant_id,
                "_tenant_namespace": tenant_namespace,
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
        tenant_id: str | None = None,
        tenant_namespaces: list[str] | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        scalar_filters = {
            "_type": memory_type.value,
            "_user_id": user_id,
            "_agent_id": agent_id,
            "_thread_id": thread_id,
            "_display_id": display_id,
            "_run_id": run_id,
            "_tenant_id": tenant_id,
        }
        filters: dict[str, str | dict[str, list[str]]] = {
            k: str(v) for k, v in scalar_filters.items() if v is not None and v != ""
        }
        if tenant_namespaces:
            filters["_tenant_namespace"] = (
                tenant_namespaces[0] if len(tenant_namespaces) == 1 else {"in": list(tenant_namespaces)}
            )
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

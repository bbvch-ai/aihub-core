from enum import Enum
from typing import Annotated

from mem0 import AsyncMemory
from mem0.configs.base import MemoryConfig
from pydantic import BaseModel, Field, AliasChoices

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.graph.PatchedMemoryGraph import PatchedMemoryGraph


class MemoryVisibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class MemoryType(Enum):
    USER_MEMORY = "user_memory"
    EXPERT_MEMORY = "expert_memory"


class Memory(BaseModel):
    id: Annotated[str, Field(description="The unique identifier for the memory.")]
    memory: Annotated[str, Field(description="The memory deduced from the text data.")]
    score: Annotated[float | None, Field(description="The score of the memory.")] = None
    created_at: Annotated[str, Field(description="The timestamp when the memory was created.")]
    user_id: Annotated[str | None, Field(description="The user ID of the user who created the memory.")]
    agent_id: Annotated[str | None, Field(description="The agent ID of the agent who created the memory.")]
    thread_id: Annotated[
        str | None, Field(description="The ID of the thread in which the memory was created.", alias="run_id")
    ]


class MemoryRelation(BaseModel):
    """Represents a knowledge graph triple"""

    source: Annotated[str, Field(description="The source entity.")]
    relation: Annotated[
        str,
        Field(
            description="The relationship between the source and target entities.",
            validation_alias=AliasChoices("relationship", "relation"),
        ),
    ]
    target: Annotated[
        str, Field(description="The target entity.", validation_alias=AliasChoices("target", "destination"))
    ]


class MemorySearchResult(BaseModel):
    results: Annotated[list[Memory], Field(description="The list of matching memories.")]
    relations: Annotated[list[MemoryRelation], Field(description="The list of matching memory relations.")]


class Mem0Service:

    def __init__(
        self,
        config: MemoryConfig,
        t: LocaleHandler,
    ):
        self._config = config
        self._memory = AsyncMemory(config=config)
        self._memory.graph = PatchedMemoryGraph.from_graph(self._memory.graph, t=t)

    @property
    def config(self):
        return self._config

    async def add_memory(
        self,
        messages: list[dict[str, str]],
        thread_id: str,
        display_id: str,
        run_id: str,
        memory_type: MemoryType,
        user_id: str | None = None,
        agent_id: str | None = None,
        public: bool = False,
        expert_memory_database: str | None = None,
        expert_memory_namespace: str | None = None,
        infer: bool = True,
    ):
        await self._memory.add(
            messages,
            user_id=user_id,
            agent_id=agent_id,
            run_id=thread_id,  # Not a bug - a run in mem0 is what we consider to be a thread
            metadata={
                "thread_id": thread_id,
                "display_id": display_id,
                "run_id": run_id,
                "visibility": MemoryVisibility.PUBLIC.value if public else MemoryVisibility.PRIVATE.value,
                "type": memory_type,
                "expert_memory_database": expert_memory_database,
                "expert_memory_namespace": expert_memory_namespace,
            },
            infer=infer,
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
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        memory_type: MemoryType | None = None,
        user_id: str | None = None,
        agent_id: str | None = None,
        public: bool | None = None,
        expert_memory_database: str | None = None,
        expert_memory_namespace: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        filters = {
            "thread_id": thread_id,
            "display_id": display_id,
            "run_id": run_id,
            "visibility": MemoryVisibility.PUBLIC.value if public else MemoryVisibility.PRIVATE.value,
            "type": memory_type,
            "expert_memory_database": expert_memory_database,
            "expert_memory_namespace": expert_memory_namespace,
        }
        filters = {k: str(v) for k, v in filters.items() if v is not None}
        memories = await self._memory.search(
            query=query,
            user_id=user_id,
            agent_id=agent_id,
            run_id=thread_id,  # Not a bug - a run in mem0 is what we consider to be a thread
            limit=limit,
            filters=filters,
            threshold=threshold,
            rerank=rerank,
        )
        return MemorySearchResult.model_validate(memories)

    async def delete_all(
        self,
        user_id: str,
        agent_id: str | None = None,
        thread_id: str | None = None,
    ):
        await self._memory.delete_all(user_id=user_id, agent_id=agent_id, run_id=thread_id)

    async def get_all(
        self,
        user_id: str,
        agent_id: str | None = None,
    ) -> MemorySearchResult:
        memories = await self._memory.get_all(user_id=user_id, agent_id=agent_id, limit=10_000)
        return MemorySearchResult.model_validate(memories)

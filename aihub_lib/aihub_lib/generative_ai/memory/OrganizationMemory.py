from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.Mem0Service import Mem0Service
from aihub_lib.infrastructure.mem0.Mem0Settings import Mem0Settings
from aihub_lib.infrastructure.mem0.types.MemorySearchResult import MemorySearchResult
from aihub_lib.infrastructure.mem0.types.MemoryType import MemoryType


class OrganizationMemory:
    def __init__(self, organization_name: str, t: LocaleHandler):
        self._config = Mem0Settings().get_config()
        self._organization_name = organization_name
        self._t = t
        self.mem0service = Mem0Service(
            self._config,
            t=self._t,
        )

    @property
    def owner_id(self):
        return self._organization_name

    async def delete_all(
        self,
    ):
        return await self.mem0service.delete_all(owner_id=self.owner_id)

    async def get_all(self) -> MemorySearchResult:
        return await self.mem0service.get_all(owner_id=self.owner_id)

    async def delete_memory(self, memory_id: str):
        return await self.mem0service.delete_memory(memory_id=memory_id)

    async def update_memory(self, memory_id: str, data: str):
        return await self.mem0service.update_memory(memory_id=memory_id, data=data)

    async def search_organization_memory(
        self,
        query: str,
        organization_namespace: str | None = None,
        agent_id: str | None = None,
        user_id: str | None = None,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        return await self.mem0service.search(
            query=query,
            owner_id=self.owner_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            memory_type=MemoryType.ORGANIZATION_MEMORY,
            user_id=user_id,
            agent_id=agent_id,
            organization_namespace=organization_namespace,
            organization_name=self._organization_name,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

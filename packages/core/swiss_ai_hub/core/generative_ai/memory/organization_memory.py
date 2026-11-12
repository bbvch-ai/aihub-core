from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.mem0_service import Mem0Service
from swiss_ai_hub.core.infrastructure.mem0.mem0_settings import Mem0Settings
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType


class OrganizationMemory:
    """
    Provides tenant-scoped memory management for shared knowledge across users.

    Tenant memories differ from user memories in scope - they're accessible to all users within
    a tenant. Use this for managing company-wide facts, policies, or shared context that should
    inform all agents serving the tenant. Every operation is confined to `tenant_id`, which the
    API takes from the tenant the caller acts within, so one tenant never sees another's memories.
    """

    def __init__(self, tenant_id: str, t: LocaleHandler):
        settings = Mem0Settings()
        self._config = settings.get_config()
        self._tenant_id = tenant_id
        self._t = t
        self.mem0service = Mem0Service(
            self._config,
            t=self._t,
            max_search_query_tokens=settings.SEARCH_QUERY_EMBEDDING_WINDOW,
        )

    @property
    def owner_id(self) -> str:
        """Returns the tenant ID as the owner for memory scoping."""
        return self._tenant_id

    async def delete_all(self):
        """Deletes all organization memories. Use with caution - affects all users in the org."""
        return await self.mem0service.delete_all(owner_id=self.owner_id)

    async def get_all(self) -> MemorySearchResult:
        """Retrieves all organization memories without filtering. Used for admin UI viewing."""
        return await self.mem0service.get_all(owner_id=self.owner_id)

    async def delete_memory(self, memory_id: str) -> None:
        """Deletes one of this tenant's memories; raises `MemoryNotFoundError` for a memory of any other scope."""
        await self.mem0service.delete_memory(
            memory_id=memory_id, owner_id=self.owner_id, memory_type=MemoryType.ORGANIZATION_MEMORY
        )

    async def update_memory(self, memory_id: str, data: str) -> None:
        """Rewrites one of this tenant's memories; raises `MemoryNotFoundError` for a memory of any other scope."""
        await self.mem0service.update_memory(
            memory_id=memory_id, owner_id=self.owner_id, memory_type=MemoryType.ORGANIZATION_MEMORY, data=data
        )

    async def adopt_memories_of(self, previous_tenant_id: str) -> int:
        """Moves the memories stored under `previous_tenant_id` into this tenant and returns how many moved."""
        return await self.mem0service.reassign_organization_memories(
            from_tenant_id=previous_tenant_id, to_tenant_id=self.owner_id
        )

    async def search_organization_memory(
        self,
        query: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        tenant_namespaces: list[str] | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        """
        Searches tenant memories semantically. Pass `tenant_namespaces` to restrict to one or more
        namespaces; pass None or empty for unscoped retrieval.
        """
        return await self.mem0service.search(
            query=query,
            owner_id=self.owner_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            memory_type=MemoryType.ORGANIZATION_MEMORY,
            user_id=user_id,
            agent_id=agent_id,
            tenant_namespaces=tenant_namespaces,
            tenant_id=self._tenant_id,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

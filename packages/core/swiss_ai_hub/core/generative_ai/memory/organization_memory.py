from swiss_ai_hub.core.generative_ai.memory.memory_settings import MemorySettings
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
    inform all agents serving the tenant. Tenant scoping replaces organization scoping for multi-tenancy support.
    """

    def __init__(self, t: LocaleHandler):
        """Initialize tenant memory manager using default tenant from settings."""
        self._config = Mem0Settings().get_config()
        self._tenant_id = MemorySettings().DEFAULT_TENANT_ID
        self._tenant_namespace = MemorySettings().DEFAULT_TENANT_NAMESPACE
        self._t = t
        self.mem0service = Mem0Service(
            self._config,
            t=self._t,
        )

    @property
    def owner_id(self):
        """Returns the tenant ID as the owner for memory scoping."""
        return self._tenant_id

    async def delete_all(self):
        """Deletes all organization memories. Use with caution - affects all users in the org."""
        return await self.mem0service.delete_all(owner_id=self.owner_id)

    async def get_all(self) -> MemorySearchResult:
        """Retrieves all organization memories without filtering. Used for admin UI viewing."""
        return await self.mem0service.get_all(owner_id=self.owner_id)

    async def delete_memory(self, memory_id: str):
        """Deletes a specific organization memory by ID."""
        return await self.mem0service.delete_memory(memory_id=memory_id)

    async def update_memory(self, memory_id: str, data: str):
        """Updates the text content of a specific organization memory."""
        return await self.mem0service.update_memory(memory_id=memory_id, data=data)

    async def search_organization_memory(
        self,
        query: str,
        agent_id: str | None = None,
        user_id: str | None = None,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        """
        Searches tenant memories semantically.
        Tenant ID and namespace are from settings (not user-controllable).
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
            tenant_namespace=self._tenant_namespace,
            tenant_id=self._tenant_id,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

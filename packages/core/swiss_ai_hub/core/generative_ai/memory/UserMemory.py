from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.Mem0Service import Mem0Service
from swiss_ai_hub.core.infrastructure.mem0.Mem0Settings import Mem0Settings
from swiss_ai_hub.core.infrastructure.mem0.types.MemorySearchResult import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.MemoryType import MemoryType


class UserMemory:
    """
    Provides user-scoped memory management for direct CRUD operations on user memories.

    Unlike AgentMemory (which wraps memories with agent context), this class manages raw user memories
    directly. Use this for administrative operations like viewing all user memories, bulk deletion,
    or manual memory editing via the UI/API.
    """

    def __init__(self, user: UserIdentity, t: LocaleHandler):
        """Initialize user memory manager for a specific user."""
        self._config = Mem0Settings().get_config()
        self._user = user
        self._t = t
        self.mem0service = Mem0Service(
            self._config,
            t=self._t,
        )

    @property
    def owner_id(self):
        """Returns the user ID as the owner for memory scoping."""
        return self._user.id

    async def delete_all(self):
        """Deletes all memories for this user. Used for data cleanup or privacy requests (GDPR)."""
        return await self.mem0service.delete_all(owner_id=self.owner_id)

    async def get_all(self) -> MemorySearchResult:
        """Retrieves all memories for this user without filtering. Used for admin UI memory viewing."""
        return await self.mem0service.get_all(owner_id=self.owner_id)

    async def delete_memory(self, memory_id: str):
        """Deletes a specific memory by ID. Used when users want to remove incorrect or outdated facts."""
        return await self.mem0service.delete_memory(memory_id=memory_id)

    async def update_memory(self, memory_id: str, data: str):
        """Updates the text content of a specific memory. Preserves metadata while changing the fact itself."""
        return await self.mem0service.update_memory(memory_id=memory_id, data=data)

    async def search_user_memory(
        self,
        query: str,
        agent_id: str | None = None,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        """
        Searches user memories semantically, optionally filtered by agent/thread/display/run context.

        Unlike get_all(), this performs semantic search based on query relevance rather than returning
        everything. Useful for memory exploration in UI or debugging why certain memories are/aren't retrieved.
        """
        return await self.mem0service.search(
            query=query,
            owner_id=self.owner_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            memory_type=MemoryType.USER_MEMORY,
            user_id=self._user.id,
            agent_id=agent_id,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

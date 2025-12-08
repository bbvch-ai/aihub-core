from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.Mem0Service import Mem0Service, MemorySearchResult
from aihub_lib.infrastructure.mem0.Mem0Settings import Mem0Settings


class UserMemory:
    def __init__(self, user: UserIdentity, t: LocaleHandler):
        self._config = Mem0Settings().get_config()
        self._user = user
        self._t = t
        self.mem0service = Mem0Service(
            self._config,
            t=self._t,
        )

    @property
    def user_id(self):
        return self._user.id

    async def delete_all(
        self,
    ):
        return await self.mem0service.delete_all(user_id=self.user_id)

    async def get_all(self) -> MemorySearchResult:
        return await self.mem0service.get_all(user_id=self.user_id)

    async def delete_memory(self, memory_id: str):
        return await self.mem0service.delete_memory(memory_id=memory_id)

    async def update_memory(self, memory_id: str, data: str):
        return await self.mem0service.update_memory(memory_id=memory_id, data=data)

    async def search(
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
        return await self.mem0service.search(
            query=query,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            user_id=self.user_id,
            agent_id=agent_id,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

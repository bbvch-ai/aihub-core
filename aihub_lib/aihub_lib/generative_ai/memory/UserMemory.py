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
        agent_id: str | None = None,
        thread_id: str | None = None,
    ):
        return await self.mem0service.delete_all(user_id=self.user_id, agent_id=agent_id, thread_id=thread_id)

    async def get_all(self, agent_id: str | None = None) -> MemorySearchResult:
        return await self.mem0service.get_all(user_id=self.user_id, agent_id=agent_id)

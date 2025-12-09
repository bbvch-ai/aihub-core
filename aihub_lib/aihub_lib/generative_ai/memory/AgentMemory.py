from datetime import datetime

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.Mem0Service import Mem0Service
from aihub_lib.infrastructure.mem0.types.MemoryAdded import MemoryAdded
from aihub_lib.infrastructure.mem0.types.MemorySearchResult import MemorySearchResult
from aihub_lib.infrastructure.mem0.types.MemoryType import MemoryType
from aihub_lib.infrastructure.mem0.Mem0Settings import Mem0Settings


class AgentMemory:
    def __init__(self, agent_config: AgentConfig, t: LocaleHandler):
        custom_fact_extraction_prompt = t(
            "lib.prompt.memory.fact_extraction",
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )
        custom_update_memory_prompt = t(
            "lib.prompt.memory.memory_update",
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
        )

        self._agent_config = agent_config
        self._t = t
        self._config = Mem0Settings().get_config(
            custom_fact_extraction_prompt=custom_fact_extraction_prompt,
            custom_update_memory_prompt=custom_update_memory_prompt,
        )
        self.mem0service = Mem0Service(
            self._config,
            t=self._t,
        )

    @property
    def agent_id(self):
        return f"{self._agent_config.agent_class}/{self._agent_config.agent_id}"

    def messages_to_dict(
        self, messages: list[ChatMessage], user_id: str, remove_system_message: bool = True
    ) -> list[dict[str, str]]:
        conversation: list[dict[str, str]] = []
        for msg in messages:
            name = user_id if msg.role == MessageRole.USER else self.agent_id
            if remove_system_message and msg.role == MessageRole.SYSTEM:
                continue
            conversation.append({"role": msg.role.value, "content": msg.content, "name": name})
        return conversation

    async def add_user_memory(
        self,
        messages: list[ChatMessage],
        user_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
    ) -> MemoryAdded:
        return await self.mem0service.add_memory(
            messages=self.messages_to_dict(messages, user_id),
            owner_id=user_id,
            memory_type=MemoryType.USER_MEMORY,
            user_id=user_id,
            agent_id=self.agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
        )

    async def add_organization_memory(
        self,
        messages: list[ChatMessage],
        user_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        organization_name: str,
        organization_namespace: str,
    ) -> MemoryAdded:
        return await self.mem0service.add_memory(
            messages=self.messages_to_dict(messages, user_id),
            owner_id=organization_name,
            memory_type=MemoryType.ORGANIZATION_MEMORY,
            user_id=user_id,
            agent_id=self.agent_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            organization_name=organization_name,
            organization_namespace=organization_namespace,
        )

    async def search_user_memory(
        self,
        query: str,
        user_id: str,
        thread_id: str | None = None,
        display_id: str | None = None,
        run_id: str | None = None,
        limit: int = 100,
        threshold: float | None = None,
        rerank: bool = True,
    ) -> MemorySearchResult:
        return await self.mem0service.search(
            query=query,
            owner_id=user_id,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            memory_type=MemoryType.USER_MEMORY,
            user_id=user_id,
            agent_id=self.agent_id,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

    async def search_organization_memory(
        self,
        query: str,
        organization_name: str,
        organization_namespace: str | None = None,
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
            owner_id=organization_name,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
            memory_type=MemoryType.ORGANIZATION_MEMORY,
            user_id=user_id,
            agent_id=self.agent_id,
            organization_namespace=organization_namespace,
            organization_name=organization_name,
            limit=limit,
            threshold=threshold,
            rerank=rerank,
        )

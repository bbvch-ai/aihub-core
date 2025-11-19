from datetime import datetime
from enum import Enum

from llama_index.core.base.llms.types import ChatMessage
from mem0 import AsyncMemory

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.mem0.Mem0Settings import Mem0Settings


class MemoryVisibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class MemoryType(Enum):
    USER_MEMORY = "user_memory"
    EXPERT_MEMORY = "expert_memory"


class Mem0Service:

    def __init__(self, agent_config: AgentConfig, t: LocaleHandler):
        custom_fact_extraction_prompt = t(
            "lib.prompt.memory.custom_fact_extraction",
            agent_name=agent_config.name,
            agent_description=agent_config.description,
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )
        custom_update_memory_prompt = t(
            "lib.prompt.memory.custom_update_memory",
            agent_name=agent_config.name,
            agent_description=agent_config.description,
        )
        custom_entity_extraction_prompt = t(
            "lib.prompt.memory.custom_entity_extraction",
            agent_name=agent_config.name,
            agent_description=agent_config.description,
        )
        self._agent_config = agent_config
        self._t = t
        self._config = Mem0Settings().get_config(
            custom_fact_extraction_prompt=custom_fact_extraction_prompt,
            custom_update_memory_prompt=custom_update_memory_prompt,
            custom_entity_extraction_prompt=custom_entity_extraction_prompt,
        )
        self._memory = AsyncMemory(config=self._config)

    async def add_user_memory(
        self,
        messages: list[ChatMessage],
        user_id: str,
        thread_id: str,
        display_id: str,
        run_id: str,
        public: bool = False,
    ):
        agent_id = f"{self._agent_config.agent_class}/{self._agent_config.agent_id}"

        conversation: list[dict[str, str]] = []
        for msg in messages:
            name = user_id if msg.role == "user" else agent_id
            conversation.append({"role": str(msg.role), "content": msg.content, "name": name})

        await self._memory.add(
            conversation,
            user_id=user_id,
            agent_id=agent_id,
            run_id="1",
            metadata={
                "thread_id": thread_id,
                "display_id": display_id,
                "run_id": run_id,
                "visibility": MemoryVisibility.PUBLIC if public else MemoryVisibility.PRIVATE,
                "type": MemoryType.USER_MEMORY,
                "expert_memory_database": "1",
                "expert_memory_namespace": "my-namespace",
            },
        )

from typing import List

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer

from aihub_agent.agents.rag.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_agent.agents.rag.LimitChatHistoryStepConfig import LimitChatHistoryStepConfig


def limit_chat_history_step(
    config: LimitChatHistoryStepConfig, chat_history: List[ChatMessage]
) -> LimitChatHistoryEvent:
    memory = ChatMemoryBuffer.from_defaults(
        chat_history=chat_history,
        token_limit=config.number_of_input_tokens,
    )
    return LimitChatHistoryEvent(limited_history=memory.get())

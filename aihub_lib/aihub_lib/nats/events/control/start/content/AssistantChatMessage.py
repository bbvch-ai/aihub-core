from llama_index.core.base.llms.types import ChatMessage


class AssistantChatMessage(ChatMessage):
    agent_id: str
    agent_class: str

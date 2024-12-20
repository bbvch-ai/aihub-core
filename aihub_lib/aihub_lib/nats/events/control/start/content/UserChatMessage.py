from llama_index.core.base.llms.types import ChatMessage


class UserChatMessage(ChatMessage):
    user_id: str

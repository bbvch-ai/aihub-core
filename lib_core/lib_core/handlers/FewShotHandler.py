from typing import List, TypedDict

from llama_index.core.base.llms.types import ChatMessage, MessageRole


class HistoryItem(TypedDict):
    user: str
    assistant: str


class ChatHistory(TypedDict):
    system: str
    history: List[HistoryItem]


class FewShotHandler:
    @staticmethod
    def chat_history_from_dict(
        few_shot_dict: ChatHistory, last_user_message: str
    ) -> List[ChatMessage]:
        few_shot_messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=few_shot_dict["system"],
            )
        ]
        for few_shot in few_shot_dict["history"]:
            few_shot_messages.append(
                ChatMessage(
                    role=MessageRole.USER,
                    content=few_shot["user"],
                )
            )
            few_shot_messages.append(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=few_shot["assistant"],
                )
            )
        few_shot_messages.append(
            ChatMessage(
                role=MessageRole.USER,
                content=last_user_message,
            )
        )
        return few_shot_messages

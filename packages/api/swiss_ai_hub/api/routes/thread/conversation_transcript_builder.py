from typing import Any, Literal, cast

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartInputAudioParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel, Field

ContentPart = (
    ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam | ChatCompletionContentPartInputAudioParam
)


class _ProjectedMessage(BaseModel):
    role: Literal["user", "assistant"]
    display_id: str
    content: list[ContentPart] = Field(default_factory=list)


class ConversationTranscriptBuilder:
    """Accumulates projected user/assistant turns per display into OpenAI chat messages."""

    def __init__(self) -> None:
        self.messages: list[_ProjectedMessage] = []
        self.assistant_text_by_display: dict[str, str] = {}

    def add_user_parts(self, display_id: str, parts: list[ContentPart]) -> None:
        self.assistant_text_by_display[display_id] = ""
        if not parts:
            raise ValueError("User event has no supported content")

        if self.messages and self.messages[-1].role == "user" and self.messages[-1].display_id == display_id:
            self.messages[-1].content.extend(parts)
            return
        self.messages.append(_ProjectedMessage(role="user", display_id=display_id, content=parts))

    def add_assistant_text(self, display_id: str, text: str) -> None:
        if not text:
            raise ValueError("Assistant event has no text")

        if self.messages and self.messages[-1].role == "assistant" and self.messages[-1].display_id == display_id:
            current = self.messages[-1]
            if current.content and current.content[-1]["type"] == "text":
                current.content[-1]["text"] += text
            else:
                current.content.append(ChatCompletionContentPartTextParam(type="text", text=text))
        else:
            self.messages.append(
                _ProjectedMessage(
                    role="assistant",
                    display_id=display_id,
                    content=[ChatCompletionContentPartTextParam(type="text", text=text)],
                )
            )
        self.assistant_text_by_display[display_id] = self.assistant_text_by_display.get(display_id, "") + text

    def start_user_segment(self, display_id: str) -> None:
        self.assistant_text_by_display[display_id] = ""

    def streamed_assistant_text(self, display_id: str) -> str:
        return self.assistant_text_by_display.get(display_id, "")

    def to_openai_messages(self) -> list[ChatCompletionMessageParam]:
        result: list[ChatCompletionMessageParam] = []
        for message in self.messages:
            if message.role == "user":
                result.append(
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=cast(Any, message.content),
                    )
                )
            else:
                result.append(
                    ChatCompletionAssistantMessageParam(
                        role="assistant",
                        content=cast(Any, message.content),
                    )
                )
        return result

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, cast

from llama_index.core.base.llms.types import AudioBlock, ChatMessage, ImageBlock, TextBlock
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartInputAudioParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL
from openai.types.chat.chat_completion_content_part_input_audio_param import InputAudio
from pydantic import ValidationError
from swiss_ai_hub.core.events.agent import Message
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity

logger = logging.getLogger(__name__)

DeliveryKey = tuple[str, str, str, str, str, str, str, str]
ContentPart = (
    ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam | ChatCompletionContentPartInputAudioParam
)
_VISIBLE_MARKER_PARENTS = {"UserMessageEvent", "HumanInTheLoopResponseEvent"}
_PROJECTABLE_PARENTS = {
    "UserMessageEvent",
    "HumanInTheLoopResponseEvent",
    "ChunkEvent",
    "HumanInTheLoopRequestEvent",
    "StopEvent",
}


@dataclass
class _ProjectedMessage:
    role: Literal["user", "assistant"]
    display_id: str
    content: list[ContentPart] = field(default_factory=list)


class _TranscriptBuilder:
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


def _warning_context(event: PersistedAgentEventEntity, error_type: str) -> dict[str, str]:
    return {
        "thread_id": str(getattr(event, "thread_id", "")),
        "display_id": str(getattr(event, "display_id", "")),
        "run_id": str(getattr(event, "run_id", "")),
        "event_id": str(getattr(event, "event_id", "")),
        "event_name": str(getattr(event, "event_name", "")),
        "error_type": error_type,
    }


def _warn_malformed(event: PersistedAgentEventEntity, error: Exception) -> None:
    logger.warning(
        "Skipping malformed visible history event",
        extra=_warning_context(event, type(error).__name__),
    )


def _required_string(event: PersistedAgentEventEntity, field_name: str) -> str:
    value = getattr(event, field_name, None)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing {field_name}")
    return value


def _delivery_key(event: PersistedAgentEventEntity) -> DeliveryKey:
    return (
        _required_string(event, "agent_class"),
        _required_string(event, "agent_id"),
        _required_string(event, "thread_id"),
        _required_string(event, "display_id"),
        _required_string(event, "run_id"),
        _required_string(event, "event_type"),
        _required_string(event, "event_name"),
        _required_string(event, "event_id"),
    )


def _parent_names(event: PersistedAgentEventEntity) -> set[str]:
    parents = event.event_parents
    if not isinstance(parents, list):
        return set()
    return {parent for parent in parents if isinstance(parent, str)}


def _visible_projectable_events(
    events: Iterable[PersistedAgentEventEntity],
) -> list[PersistedAgentEventEntity]:
    candidates = list(events)
    visible_display_ids = {
        event.display_id
        for event in candidates
        if event.agent_class == "UserAgent"
        and isinstance(event.display_id, str)
        and _parent_names(event) & _VISIBLE_MARKER_PARENTS
    }
    return [
        event
        for event in candidates
        if event.display_id in visible_display_ids and _parent_names(event) & _PROJECTABLE_PARENTS
    ]


def _created_at(event: PersistedAgentEventEntity) -> int:
    event_data = event.event_data
    if not isinstance(event_data, Mapping):
        raise TypeError("Event data is not a mapping")
    created_at = event_data.get("created_at")
    if isinstance(created_at, bool) or not isinstance(created_at, int):
        raise TypeError("Event created_at is not an integer")
    return created_at


def _ordered_unique_events(
    events: Iterable[PersistedAgentEventEntity],
) -> list[PersistedAgentEventEntity]:
    unique: dict[DeliveryKey, tuple[int, PersistedAgentEventEntity]] = {}
    for event in events:
        try:
            key = _delivery_key(event)
            created_at = _created_at(event)
        except (TypeError, ValueError) as error:
            _warn_malformed(event, error)
            continue
        unique.setdefault(key, (created_at, event))

    return [
        event
        for _, event in sorted(
            unique.values(),
            key=lambda item: (item[0], item[1].event_id, _delivery_key(item[1])),
        )
    ]


def _normalized_binary(value: Any) -> Any:
    if isinstance(value, list) and all(
        isinstance(byte, int) and not isinstance(byte, bool) and 0 <= byte <= 255 for byte in value
    ):
        return bytes(value)
    return value


def _last_chat_message(event: PersistedAgentEventEntity) -> ChatMessage:
    event_data = event.event_data
    if not isinstance(event_data, Mapping):
        raise TypeError("Event data is not a mapping")
    raw_messages = event_data.get("messages")
    if not isinstance(raw_messages, list) or not raw_messages:
        raise ValueError("User event has no messages")
    raw_message = raw_messages[-1]
    if not isinstance(raw_message, Mapping):
        raise TypeError("Last user message is not a mapping")

    normalized_message = dict(raw_message)
    raw_blocks = normalized_message.get("blocks")
    if not isinstance(raw_blocks, list):
        raise TypeError("Last user message blocks are not a list")

    normalized_blocks: list[dict[str, Any]] = []
    for raw_block in raw_blocks:
        if not isinstance(raw_block, Mapping):
            raise TypeError("User message block is not a mapping")
        block = dict(raw_block)
        block_type = block.get("block_type")
        if block_type not in {"text", "image", "audio"}:
            continue
        if block_type == "image":
            block["image"] = _normalized_binary(block.get("image"))
        elif block_type == "audio":
            block["audio"] = _normalized_binary(block.get("audio"))
        normalized_blocks.append(block)

    normalized_message["blocks"] = normalized_blocks
    return ChatMessage.model_validate(normalized_message)


def _user_content_parts(event: PersistedAgentEventEntity) -> list[ContentPart]:
    parts: list[ContentPart] = []
    for block in _last_chat_message(event).blocks:
        if isinstance(block, TextBlock) and block.text:
            parts.append(ChatCompletionContentPartTextParam(type="text", text=block.text))
        elif isinstance(block, ImageBlock) and block.url:
            parts.append(
                ChatCompletionContentPartImageParam(
                    type="image_url",
                    image_url=ImageURL(url=str(block.url)),
                )
            )
        elif isinstance(block, AudioBlock):
            if block.format not in {"wav", "mp3"}:
                if block.audio is not None:
                    logger.warning(
                        "Skipping visible history audio block with unsupported format",
                        extra={
                            **_warning_context(event, "UnsupportedAudioFormat"),
                            "audio_format": str(block.format),
                        },
                    )
                continue
            if isinstance(block.audio, bytes):
                audio_format = cast(Literal["wav", "mp3"], block.format)
                parts.append(
                    ChatCompletionContentPartInputAudioParam(
                        type="input_audio",
                        input_audio=InputAudio(data=block.audio.decode("ascii"), format=audio_format),
                    )
                )
    return parts


def _required_text(event: PersistedAgentEventEntity, field_name: str) -> str:
    event_data = event.event_data
    if not isinstance(event_data, Mapping):
        raise TypeError("Event data is not a mapping")
    text = event_data.get(field_name)
    if not isinstance(text, str) or not text:
        raise ValueError(f"Event has no {field_name}")
    return text


def _hitl_response_text(event: PersistedAgentEventEntity) -> str:
    event_data = event.event_data
    if not isinstance(event_data, Mapping):
        raise TypeError("Event data is not a mapping")
    response = event_data.get("response")
    if isinstance(response, bool):
        return "true" if response else "false"
    if not isinstance(response, str) or not response:
        raise ValueError("Event has no response")
    return response


def _terminal_output_text(event: PersistedAgentEventEntity) -> str:
    event_data = event.event_data
    if not isinstance(event_data, Mapping):
        raise TypeError("Event data is not a mapping")
    output_messages = event_data.get("output_messages")
    if not isinstance(output_messages, list) or not output_messages:
        return ""
    return Message.model_validate(output_messages[-1]).content


def _missing_suffix(streamed: str, full_answer: str) -> str:
    if full_answer and full_answer.startswith(streamed):
        return full_answer[len(streamed) :]
    return "" if streamed else full_answer


def project_conversation_history(
    events: Iterable[PersistedAgentEventEntity],
    *,
    primary_agent_class: str | None = None,
    primary_agent_id: str | None = None,
) -> list[ChatCompletionMessageParam]:
    """Project persisted client-visible events into the OpenAI chat message surface."""
    transcript = _TranscriptBuilder()

    for event in _ordered_unique_events(_visible_projectable_events(events)):
        parents = _parent_names(event)
        try:
            if event.agent_class == "UserAgent" and "UserMessageEvent" in parents:
                transcript.start_user_segment(event.display_id)
                transcript.add_user_parts(event.display_id, _user_content_parts(event))
            elif event.agent_class == "UserAgent" and "HumanInTheLoopResponseEvent" in parents:
                transcript.start_user_segment(event.display_id)
                transcript.add_user_parts(
                    event.display_id,
                    [ChatCompletionContentPartTextParam(type="text", text=_hitl_response_text(event))],
                )
            elif "ChunkEvent" in parents:
                transcript.add_assistant_text(event.display_id, _required_text(event, "content"))
            elif "HumanInTheLoopRequestEvent" in parents:
                transcript.add_assistant_text(event.display_id, _required_text(event, "question"))
            elif (
                "StopEvent" in parents
                and primary_agent_class is not None
                and primary_agent_id is not None
                and event.agent_class == primary_agent_class
                and event.agent_id == primary_agent_id
            ):
                full_answer = _terminal_output_text(event)
                suffix = _missing_suffix(transcript.streamed_assistant_text(event.display_id), full_answer)
                if suffix:
                    transcript.add_assistant_text(event.display_id, suffix)
        except (KeyError, TypeError, ValueError, ValidationError) as error:
            _warn_malformed(event, error)

    return transcript.to_openai_messages()

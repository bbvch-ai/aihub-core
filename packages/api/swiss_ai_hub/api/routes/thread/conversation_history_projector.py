import logging
from collections.abc import Iterable, Mapping
from typing import Any, Literal, cast

from llama_index.core.base.llms.types import AudioBlock, ChatMessage, ContentBlock, ImageBlock, TextBlock
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartInputAudioParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
)
from openai.types.chat.chat_completion_content_part_image_param import ImageURL
from openai.types.chat.chat_completion_content_part_input_audio_param import InputAudio
from pydantic import ValidationError
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.routes import ChatService

from swiss_ai_hub.api.routes.thread.conversation_transcript_builder import ContentPart, ConversationTranscriptBuilder

logger = logging.getLogger(__name__)

DeliveryKey = tuple[str, str, str, str, str, str, str, str]
_VISIBLE_MARKER_PARENTS = {"UserMessageEvent", "HumanInTheLoopResponseEvent"}
_PROJECTABLE_PARENTS = {
    "UserMessageEvent",
    "HumanInTheLoopResponseEvent",
    "ChunkEvent",
    "HumanInTheLoopRequestEvent",
    "StopEvent",
}


class ConversationHistoryProjector:
    """Projects persisted client-visible events into the OpenAI chat message surface."""

    @staticmethod
    def _warning_context(event: PersistedAgentEventEntity, error_type: str) -> dict[str, str]:
        return {
            "thread_id": str(getattr(event, "thread_id", "")),
            "display_id": str(getattr(event, "display_id", "")),
            "run_id": str(getattr(event, "run_id", "")),
            "event_id": str(getattr(event, "event_id", "")),
            "event_name": str(getattr(event, "event_name", "")),
            "error_type": error_type,
        }

    @staticmethod
    def _warn_malformed(event: PersistedAgentEventEntity, error: Exception) -> None:
        logger.warning(
            "Skipping malformed visible history event",
            extra=ConversationHistoryProjector._warning_context(event, type(error).__name__),
        )

    @staticmethod
    def _required_string(event: PersistedAgentEventEntity, field_name: str) -> str:
        value = getattr(event, field_name, None)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Missing {field_name}")
        return value

    @staticmethod
    def _delivery_key(event: PersistedAgentEventEntity) -> DeliveryKey:
        return (
            ConversationHistoryProjector._required_string(event, "agent_class"),
            ConversationHistoryProjector._required_string(event, "agent_id"),
            ConversationHistoryProjector._required_string(event, "thread_id"),
            ConversationHistoryProjector._required_string(event, "display_id"),
            ConversationHistoryProjector._required_string(event, "run_id"),
            ConversationHistoryProjector._required_string(event, "event_type"),
            ConversationHistoryProjector._required_string(event, "event_name"),
            ConversationHistoryProjector._required_string(event, "event_id"),
        )

    @staticmethod
    def _parent_names(event: PersistedAgentEventEntity) -> set[str]:
        parents = event.event_parents
        if not isinstance(parents, list):
            return set()
        return {parent for parent in parents if isinstance(parent, str)}

    @staticmethod
    def _visible_projectable_events(
        events: Iterable[PersistedAgentEventEntity],
    ) -> list[PersistedAgentEventEntity]:
        candidates = list(events)
        visible_display_ids = {
            event.display_id
            for event in candidates
            if event.agent_class == "UserAgent"
            and isinstance(event.display_id, str)
            and ConversationHistoryProjector._parent_names(event) & _VISIBLE_MARKER_PARENTS
        }
        return [
            event
            for event in candidates
            if event.display_id in visible_display_ids
            and ConversationHistoryProjector._parent_names(event) & _PROJECTABLE_PARENTS
        ]

    @staticmethod
    def _event_data(event: PersistedAgentEventEntity) -> Mapping[str, Any]:
        event_data = event.event_data
        if not isinstance(event_data, Mapping):
            raise TypeError("Event data is not a mapping")
        return event_data

    @staticmethod
    def _created_at(event: PersistedAgentEventEntity) -> int:
        created_at = ConversationHistoryProjector._event_data(event).get("created_at")
        if isinstance(created_at, bool) or not isinstance(created_at, int):
            raise TypeError("Event created_at is not an integer")
        return created_at

    @staticmethod
    def _ordered_unique_events(
        events: Iterable[PersistedAgentEventEntity],
    ) -> list[PersistedAgentEventEntity]:
        unique: dict[DeliveryKey, tuple[int, PersistedAgentEventEntity]] = {}
        for event in events:
            try:
                key = ConversationHistoryProjector._delivery_key(event)
                created_at = ConversationHistoryProjector._created_at(event)
            except (TypeError, ValueError) as error:
                ConversationHistoryProjector._warn_malformed(event, error)
                continue
            unique.setdefault(key, (created_at, event))

        return [
            event
            for _, event in sorted(
                unique.values(),
                key=lambda item: (
                    item[0],
                    item[1].event_id,
                    ConversationHistoryProjector._delivery_key(item[1]),
                ),
            )
        ]

    @staticmethod
    def _normalized_binary(value: Any) -> Any:
        if isinstance(value, list) and all(
            isinstance(byte, int) and not isinstance(byte, bool) and 0 <= byte <= 255 for byte in value
        ):
            return bytes(value)
        return value

    @staticmethod
    def _last_chat_message(event: PersistedAgentEventEntity) -> ChatMessage:
        raw_messages = ConversationHistoryProjector._event_data(event).get("messages")
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
                block["image"] = ConversationHistoryProjector._normalized_binary(block.get("image"))
            elif block_type == "audio":
                block["audio"] = ConversationHistoryProjector._normalized_binary(block.get("audio"))
            normalized_blocks.append(block)

        normalized_message["blocks"] = normalized_blocks
        return ChatMessage.model_validate(normalized_message)

    @staticmethod
    def _audio_content_part(
        event: PersistedAgentEventEntity,
        block: AudioBlock,
    ) -> ChatCompletionContentPartInputAudioParam | None:
        if block.format not in {"wav", "mp3"}:
            if block.audio is not None:
                logger.warning(
                    "Skipping visible history audio block with unsupported format",
                    extra={
                        **ConversationHistoryProjector._warning_context(event, "UnsupportedAudioFormat"),
                        "audio_format": str(block.format),
                    },
                )
            return None
        if not isinstance(block.audio, bytes):
            return None
        audio_format = cast(Literal["wav", "mp3"], block.format)
        return ChatCompletionContentPartInputAudioParam(
            type="input_audio",
            input_audio=InputAudio(data=block.audio.decode("ascii"), format=audio_format),
        )

    @staticmethod
    def _content_part(event: PersistedAgentEventEntity, block: ContentBlock) -> ContentPart | None:
        if isinstance(block, TextBlock) and block.text:
            return ChatCompletionContentPartTextParam(type="text", text=block.text)
        if isinstance(block, ImageBlock) and block.url:
            return ChatCompletionContentPartImageParam(
                type="image_url",
                image_url=ImageURL(url=str(block.url)),
            )
        if isinstance(block, AudioBlock):
            return ConversationHistoryProjector._audio_content_part(event, block)
        return None

    @staticmethod
    def _user_content_parts(event: PersistedAgentEventEntity) -> list[ContentPart]:
        parts: list[ContentPart] = []
        for block in ConversationHistoryProjector._last_chat_message(event).blocks:
            part = ConversationHistoryProjector._content_part(event, block)
            if part is not None:
                parts.append(part)
        return parts

    @staticmethod
    def _required_text(event: PersistedAgentEventEntity, field_name: str) -> str:
        text = ConversationHistoryProjector._event_data(event).get(field_name)
        if not isinstance(text, str) or not text:
            raise ValueError(f"Event has no {field_name}")
        return text

    @staticmethod
    def _hitl_response_text(event: PersistedAgentEventEntity) -> str:
        response = ConversationHistoryProjector._event_data(event).get("response")
        if isinstance(response, bool):
            return "true" if response else "false"
        if not isinstance(response, str) or not response:
            raise ValueError("Event has no response")
        return response

    @staticmethod
    def _terminal_output_text(event: PersistedAgentEventEntity) -> str:
        output_messages = ConversationHistoryProjector._event_data(event).get("output_messages")
        if output_messages is not None and not isinstance(output_messages, list):
            raise TypeError("Event output_messages is not a list")
        return ChatService.terminal_output_text(output_messages)

    @staticmethod
    def project(
        events: Iterable[PersistedAgentEventEntity],
        *,
        primary_agent_class: str | None = None,
        primary_agent_id: str | None = None,
    ) -> list[ChatCompletionMessageParam]:
        transcript = ConversationTranscriptBuilder()

        visible_events = ConversationHistoryProjector._visible_projectable_events(events)
        for event in ConversationHistoryProjector._ordered_unique_events(visible_events):
            parents = ConversationHistoryProjector._parent_names(event)
            try:
                if event.agent_class == "UserAgent" and "UserMessageEvent" in parents:
                    transcript.start_user_segment(event.display_id)
                    transcript.add_user_parts(event.display_id, ConversationHistoryProjector._user_content_parts(event))
                elif event.agent_class == "UserAgent" and "HumanInTheLoopResponseEvent" in parents:
                    transcript.start_user_segment(event.display_id)
                    transcript.add_user_parts(
                        event.display_id,
                        [
                            ChatCompletionContentPartTextParam(
                                type="text",
                                text=ConversationHistoryProjector._hitl_response_text(event),
                            )
                        ],
                    )
                elif "ChunkEvent" in parents:
                    transcript.add_assistant_text(
                        event.display_id,
                        ConversationHistoryProjector._required_text(event, "content"),
                    )
                elif "HumanInTheLoopRequestEvent" in parents:
                    transcript.add_assistant_text(
                        event.display_id,
                        ConversationHistoryProjector._required_text(event, "question"),
                    )
                elif (
                    "StopEvent" in parents
                    and primary_agent_class is not None
                    and primary_agent_id is not None
                    and event.agent_class == primary_agent_class
                    and event.agent_id == primary_agent_id
                ):
                    full_answer = ConversationHistoryProjector._terminal_output_text(event)
                    suffix = ChatService.missing_suffix(
                        transcript.streamed_assistant_text(event.display_id),
                        full_answer,
                    )
                    if suffix:
                        transcript.add_assistant_text(event.display_id, suffix)
            except (KeyError, TypeError, ValueError, ValidationError) as error:
                ConversationHistoryProjector._warn_malformed(event, error)

        return transcript.to_openai_messages()

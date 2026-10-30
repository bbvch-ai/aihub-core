import asyncio
import functools
import logging
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Annotated, Any

import mongoengine.errors
from bson import ObjectId
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage, TextBlock
from nats.aio.client import Client as NATS

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.distributor.external_agent_event_distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.control.exception.exception_event import ExceptionEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.display.chunk_event import ChunkEvent
from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.events.agent.display.thought_event import ThoughtEvent
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_chat_request_event import (
    HumanInTheLoopChatRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_input_request_event import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_chat_response_event import (
    HumanInTheLoopChatResponseEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_input_response_event import (
    HumanInTheLoopInputResponseEvent,
)
from swiss_ai_hub.core.events.agent.hitl.response.human_in_the_loop_response_event import (
    HumanInTheLoopResponseEvent,
)
from swiss_ai_hub.core.events.agent.record_extraction.records_extracted_event import RecordsExtractedEvent
from swiss_ai_hub.core.events.agent.semantic.llm.message import Message
from swiss_ai_hub.core.events.agent.user.chat_feature import ChatFeature
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.generative_ai.resources.costs.llm_costs import LLMCosts
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_markup import ExtractedTableMarkup
from swiss_ai_hub.core.generative_ai.structured_extraction.extraction_file_store import ExtractionFileStore
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
from swiss_ai_hub.core.subscribers.agent.agent_nc_subscriber import AgentNCSubscriber
from swiss_ai_hub.core.subscribers.nc_subscriber import NCSubscriber
from swiss_ai_hub.core.topic_managers.agents.agent_thread_topic_manager import AgentThreadTopicManager
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic

logger = logging.getLogger(__name__)

# After a run's terminal event arrives, give trailing display events this long to surface before the
# consumer finishes. NCSubscriber dispatches one asyncio task per message, so the stop event's task can
# set the stop signal before a preceding chunk's task has finished enqueuing it — without this grace the
# consumer ends on the stop and silently drops those in-flight chunks.
DISPLAY_STREAM_DRAIN_GRACE_SECONDS = 0.25

_TABLE_DOWNLOAD_KEY = "lib.common.extracted_table_download"


@dataclass
class StreamingResources:
    stop_signal: asyncio.Event
    subscriber: NCSubscriber
    chunk_queue: asyncio.Queue
    stop_event: StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent | None = (
        None  # Added field to store the final StopEvent
    )
    table_downloads: list[str] = field(default_factory=list)
    costs: LLMCosts = field(default_factory=LLMCosts.from_zero)


@dataclass
class JsonResources:
    stop_signal: asyncio.Event
    subscriber: NCSubscriber
    chunk_events: list[ChunkEvent | ThoughtEvent]
    costs: LLMCosts
    model_name: str
    stop_event: StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent | None = (
        None  # Added field to store the final StopEvent
    )
    table_downloads: list[str] = field(default_factory=list)


@dataclass
class ChatContent:
    content: str
    reasoning_content: str


class ChatService:
    """
    Orchestrates chat interactions for both streaming and JSON-based endpoints.
    """

    @staticmethod
    async def iter_streamed_display_events(
        resources: StreamingResources,
        drain_grace_seconds: float = DISPLAY_STREAM_DRAIN_GRACE_SECONDS,
    ) -> AsyncGenerator[DisplayEvent]:
        """
        Yield queued display events until the run has stopped AND no event has surfaced for the drain
        grace. The grace drains trailing events whose handler tasks finish after the terminal stop's
        task sets the stop signal; ending on the bare stop signal would drop them. The subscription is
        torn down by the aggregator that handles the stop event, not here. The downloads of extracted tables are held
        back to the end, so a chunk that surfaces late still comes before them.
        """
        downloads: list[DisplayEvent] = []
        while True:
            try:
                event = await asyncio.wait_for(resources.chunk_queue.get(), timeout=drain_grace_seconds)
                resources.chunk_queue.task_done()
                if ChatService.is_table_download(event):
                    downloads.append(event)
                else:
                    yield event
            except TimeoutError:
                if resources.stop_signal.is_set():
                    for download in downloads:
                        yield download
                    return

    @staticmethod
    async def wait_for_stop_then_drain(
        resources: StreamingResources | JsonResources,
        drain_grace_seconds: float = DISPLAY_STREAM_DRAIN_GRACE_SECONDS,
    ) -> None:
        """
        Block until the run stops, then wait out the drain grace so trailing display-event handler
        tasks finish before the caller reads the collected events. The subscription is already torn
        down by the aggregator that handles the stop event.
        """
        await resources.stop_signal.wait()
        await asyncio.sleep(drain_grace_seconds)

    @staticmethod
    def _initialize_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        messages: list[ChatMessage],
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        files: list[UserUploadedFile] | None = None,
        requested_features: list[ChatFeature] | None = None,
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
        locale: str | None = None,
    ) -> tuple[ExternalAgentEvent, AgentThreadTopicManager]:
        """
        Common initialization steps for both streaming and JSON interactions.
        """
        messages = ChatService._without_earlier_tables(messages)
        thread = None
        if thread_id:
            try:
                thread = ThreadEntity.get_thread_by_id(str(thread_id))
                if not thread:
                    raise mongoengine.errors.DoesNotExist()
                if user.id not in [u.user_id for u in thread.users]:
                    raise HTTPException(status_code=403, detail="User not part of the thread")
            except mongoengine.errors.DoesNotExist:
                pass

        if not thread:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.id)],
                agents=[AgentInstanceRef(agent_class=agent_class, agent_id=agent_id)],
                thread_id=ObjectId(thread_id) or ObjectId(),
            )
        logger.debug(f"Created thread: {thread.id}")

        hitl_requests = PersistedAgentEventEntity.human_in_the_loop_request_events_for_thread(str(thread.id))
        logger.debug(f"hitl_requests: {hitl_requests}")

        hitl_responses = PersistedAgentEventEntity.human_in_the_loop_response_events_for_thread(str(thread.id))
        logger.debug(f"hitl_responses: {hitl_responses}")

        thread_id = str(thread.id)
        display_id = display_id or str(ObjectId())

        if len(hitl_requests) != len(hitl_responses):
            open_hitl_request = HumanInTheLoopRequestEvent.deserialize_event(hitl_requests[-1].event_data)
            topic = open_hitl_request.topic

            if isinstance(open_hitl_request, HumanInTheLoopInputRequestEvent):
                response_class = HumanInTheLoopInputResponseEvent
            elif isinstance(open_hitl_request, HumanInTheLoopChatRequestEvent):
                response_class = HumanInTheLoopChatResponseEvent
            else:
                raise ValueError(
                    f"Chat interaction cannot respond to HITL request of type "
                    f"{type(open_hitl_request).__name__}. Only input and chat HITL requests are "
                    f"answerable via the chat flow; confirmation requests must use the dedicated "
                    f"agent endpoints."
                )

            parent_event_names = [topic.event_name, *response_class.parent_event_names_from_class()]
            event = HumanInTheLoopResponseEvent.deserialize_event(
                {
                    "_event_name": topic.event_name,
                    "_parent_event_names": parent_event_names,
                    "response": messages[-1].content,
                    "request_event": open_hitl_request.model_dump(),
                }
            )
            display_id = event.request_event.topic.display_id
        else:
            event = UserMessageEvent(
                messages=messages,
                user=user,
                locale=locale or LocaleHandler.DEFAULT_LOCALE,
                files=files,
                requested_features=requested_features or [],
            )

        event = ExternalAgentEvent(
            thread_id=str(thread_id),
            display_id=str(display_id),
            event=event,
        )
        logger.debug(f"Created event: {event.event.event_name}")

        topic_manager = AgentThreadTopicManager(
            agent_class="*" if subscribe_to_thread else agent_class,
            agent_id="*" if subscribe_to_thread else agent_id,
            thread_id=event.thread_id,
            display_id=event.display_id,
            run_id="*",
        )
        return event, topic_manager

    @staticmethod
    @trace_fn
    async def start_stream_chat_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        messages: list[ChatMessage],
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        files: list[UserUploadedFile] | None = None,
        requested_features: list[ChatFeature] | None = None,
        locale: str | None = None,
        aihub_headers: dict[str, str] | None = None,
    ) -> StreamingResources:
        """
        Starts a streaming chat interaction and returns the resources for SSE streaming.
        """
        external_event, topic_manager = ChatService._initialize_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            thread_id=thread_id,
            display_id=display_id,
            files=files,
            requested_features=requested_features,
            subscribe_to_thread=True,
            locale=locale,
        )

        stop_signal = asyncio.Event()
        chunk_queue = asyncio.Queue()
        resources = StreamingResources(
            stop_signal=stop_signal,
            subscriber=None,  # Will be set after subscriber creation
            chunk_queue=chunk_queue,
            stop_event=None,
        )

        async def stop_streaming(event: DisplayEvent, topic: AgentInstanceTopic) -> None:
            if download := ChatService.table_downloads_chunk(resources.table_downloads, topic):
                await chunk_queue.put(download)
            resources.stop_event = event
            await subscriber.stop()
            stop_signal.set()

        async def response_aggregator(event: DisplayEvent, topic: AgentInstanceTopic):
            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id
            logger.debug(f"Received display event: {event.event_name}")
            if event.is_chunk_event:
                logger.debug(f"Received chunk event: {event.event_name}")
                await chunk_queue.put(event)
            elif table_chunk := ChatService.extracted_table_chunk(event, topic):
                await chunk_queue.put(table_chunk)
            elif event.is_hitl_request_event:
                logger.debug(f"Received HITL event: {event.event_name}")
                await stop_streaming(event, topic)
            elif event.is_stop_event and is_primary_agent:
                logger.debug("Received stop event. Stop streaming")
                await stop_streaming(event, topic)
            elif event.is_llm_cost_event:
                resources.costs += event
            elif event.is_exception_event:
                logger.warning(f"Received exception event: {event.event_name}")
                await stop_streaming(event, topic)
            if download := ChatService.extracted_table_download(event, locale):
                resources.table_downloads.append(download)

        subscriber = AgentNCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
            subscriber_name="ChatServiceStreamInteraction",
        )
        resources.subscriber = subscriber
        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction via WebSocket
        await external_agent_event_distributor.distribute_event(
            external_event,
            user,
            aihub_headers=aihub_headers,
            target_agent=AgentInstanceRef(agent_class=agent_class, agent_id=agent_id),
        )

        return resources

    @staticmethod
    @trace_fn
    async def start_json_chat_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        messages: list[ChatMessage],
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        files: list[UserUploadedFile] | None = None,
        requested_features: list[ChatFeature] | None = None,
        locale: str | None = None,
        aihub_headers: dict[str, str] | None = None,
    ) -> JsonResources:
        """
        Starts a JSON-based chat interaction, waiting for all events before returning.
        """
        external_event, topic_manager = ChatService._initialize_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            thread_id=thread_id,
            display_id=display_id,
            files=files,
            requested_features=requested_features,
            subscribe_to_thread=True,
            locale=locale,
        )
        return await ChatService.start_json_event_interaction(
            user,
            agent_class,
            agent_id,
            external_event,
            topic_manager,
            nc,
            external_agent_event_distributor,
            aihub_headers=aihub_headers,
        )

    @staticmethod
    @trace_fn
    async def start_json_event_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        external_event: ExternalAgentEvent,
        topic_manager: AgentThreadTopicManager,
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        aihub_headers: dict[str, str] | None = None,
    ):
        stop_signal = asyncio.Event()
        chunk_events: list[ChunkEvent | ThoughtEvent] = []
        costs = LLMCosts.from_zero()
        model_name = f"{agent_class}/{agent_id}"
        # A user message carries the locale the answer is written in; other start events fall back to the default.
        locale = getattr(external_event.event, "locale", None)

        resources = JsonResources(
            stop_signal=stop_signal,
            subscriber=None,  # Will be set after subscriber creation.
            chunk_events=chunk_events,
            costs=costs,
            model_name=model_name,
            stop_event=None,
        )

        async def stop_collecting(event: DisplayEvent, topic: AgentInstanceTopic) -> None:
            if download := ChatService.table_downloads_chunk(resources.table_downloads, topic):
                resources.chunk_events.append(download)
            resources.stop_event = event
            await resources.subscriber.stop()
            resources.stop_signal.set()

        async def response_aggregator(event: DisplayEvent, topic: AgentInstanceTopic):
            logger.debug(f"Received display event: {event.event_name}")
            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id
            if event.is_chunk_event:
                resources.chunk_events.append(event)
            elif table_chunk := ChatService.extracted_table_chunk(event, topic):
                resources.chunk_events.append(table_chunk)
            elif event.is_hitl_request_event:
                await stop_collecting(event, topic)
            elif event.is_stop_event and is_primary_agent:
                logger.debug("Received stop event. Stop streaming")
                await stop_collecting(event, topic)
            elif event.is_llm_cost_event:
                resources.costs += event
                resources.model_name = event.llm_name
            elif event.is_exception_event:
                logger.warning(f"Received exception event: {event.event_name}")
                await stop_collecting(event, topic)
            if download := ChatService.extracted_table_download(event, locale):
                resources.table_downloads.append(download)

        subscriber = AgentNCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
            subscriber_name="ChatServiceJsonInteraction",
        )
        resources.subscriber = subscriber

        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction
        await external_agent_event_distributor.distribute_event(
            external_event,
            user,
            aihub_headers=aihub_headers,
            target_agent=AgentInstanceRef(agent_class=agent_class, agent_id=agent_id),
        )

        return resources

    @staticmethod
    def extracted_table_text(event_data: Annotated[dict[str, Any], "A records-extracted event, dumped"]) -> str:
        """The answer text a table extracted for a tool call contributes: the model only read its summary, so a client
        that shows only answer text would otherwise never see the table."""
        if event_data.get("_event_name") != "RecordsExtractedEvent" or not event_data.get("tool_call_id"):
            return ""
        table = event_data.get("table") or ""
        return f"\n\n{table}\n\n{event_data.get('summary') or ''}\n\n" if table else ""

    @staticmethod
    def extracted_table_chunk(
        event: DisplayEvent, topic: Annotated[AgentInstanceTopic, "The agent run the event belongs to"]
    ) -> ChunkEvent | None:
        text = ChatService.extracted_table_text(
            event.model_dump(include={"table", "summary", "tool_call_id"}) | {"_event_name": event.event_name}
        )
        if not text:
            return None
        return ChunkEvent(content=text, model_name=f"{topic.agent_class}/{topic.agent_id}", created_at=event.created_at)

    @staticmethod
    def extracted_table_download(event: DisplayEvent, locale: str | None = None) -> str:
        """The line that offers the whole table of an extraction for download; empty for any other event.

        The answer only shows a preview, and a client that reads answer text has no other way to the file. The link is
        presigned, so whoever holds it can download the table until it expires: it is only made here, for the user
        whose request streams the thread.
        """
        if not isinstance(event, RecordsExtractedEvent) or event.file is None:
            return ""
        name = event.file.filename.replace("[", "\\[").replace("]", "\\]")
        url = ExtractionFileStore.download_url(event.file)
        line = LocaleHandler(locale)(_TABLE_DOWNLOAD_KEY, rows=event.file.row_count, name=name, url=url)
        return f"\n\n{line}"

    @staticmethod
    def table_downloads_chunk(
        downloads: Annotated[list[str], "Download lines collected during the run, empty for other events"],
        topic: Annotated[AgentInstanceTopic, "The agent run that ended"],
    ) -> ChunkEvent | None:
        """The downloads as the answer's last chunk: an agent streams its preview after the event naming the file."""
        text = "".join(downloads)
        if not text:
            return None
        return ChunkEvent(content=text, model_name=f"{topic.agent_class}/{topic.agent_id}")

    @staticmethod
    @functools.cache
    def _table_download_line() -> re.Pattern[str]:
        """The line that ends an answer with the download of an extracted table, in any locale the answer was given
        in, see `extracted_table_download`."""
        placeholders = {"rows": "\x00R", "name": "\x00N", "url": "\x00U"}
        patterns = {"\x00R": r"\d+", "\x00N": r"[^\n]*", "\x00U": r"[^)\s]+"}
        lines = []
        for locale in LocaleHandler().supported_locales:
            line = re.escape(LocaleHandler(locale)(_TABLE_DOWNLOAD_KEY, **placeholders))
            for placeholder, pattern in patterns.items():
                line = line.replace(re.escape(placeholder), pattern)
            lines.append(line)
        return re.compile(rf"\n*^(?:{'|'.join(lines)})[ \t]*$", re.MULTILINE)

    @staticmethod
    def is_table_download(event: DisplayEvent) -> bool:
        return isinstance(event, ChunkEvent) and ChatService._is_table_download_text(event.content)

    @staticmethod
    def _is_table_download_text(text: str) -> bool:
        return bool(text.strip()) and not ChatService._table_download_line().sub("", text).strip()

    @staticmethod
    def _without_earlier_tables(messages: list[ChatMessage]) -> list[ChatMessage]:
        """Earlier answers come back with every message; a table among them would ride on every event of the run."""
        return [ChatService._condensed(message) if message.role == "assistant" else message for message in messages]

    @staticmethod
    def _condensed(message: ChatMessage) -> ChatMessage:
        """The message with its tables condensed in its text blocks; images and other blocks are kept as they are.

        A table's download line goes too: a model handed an expiring link copies it into later answers.
        """
        blocks = [
            block.model_copy(
                update={"text": ChatService._table_download_line().sub("", ExtractedTableMarkup.condensed(block.text))}
            )
            if isinstance(block, TextBlock)
            else block
            for block in message.blocks
        ]
        if all(new == old for new, old in zip(blocks, message.blocks, strict=True)):
            return message
        return ChatMessage(role=message.role, blocks=blocks, additional_kwargs=message.additional_kwargs)

    @staticmethod
    def terminal_output_text(output_messages: list[Any] | None) -> str:
        """Return terminal answer text from live LlamaIndex/core messages or raw persisted payloads."""
        if not output_messages:
            return ""
        last_message = output_messages[-1]
        if isinstance(last_message, ChatMessage):
            return last_message.content or ""
        if isinstance(last_message, Message):
            return last_message.content
        return Message.model_validate(last_message).content

    @staticmethod
    def answer_text(parts: Annotated[list[str], "Streamed chunks, in order"]) -> str:
        """The streamed answer without the tables inserted from tool calls and their downloads: the final answer never
        holds them, so they would keep it from extending what was streamed."""
        return "".join(
            part
            for part in parts
            if ExtractedTableMarkup.condensed(part) == part and not ChatService._is_table_download_text(part)
        )

    @staticmethod
    def missing_suffix(streamed: str, full_answer: str) -> str:
        """Return the unstreamed suffix when the full answer extends the streamed prefix."""
        if full_answer and full_answer.startswith(streamed):
            return full_answer[len(streamed) :]
        return "" if streamed else full_answer

    @staticmethod
    @trace_fn
    def build_json_response_content(
        chunk_events: list[ChunkEvent | ThoughtEvent], stop_event: StopEvent | HumanInTheLoopRequestEvent | None
    ) -> ChatContent:
        """Construct a JSON response from collected chunk events; the downloads of extracted tables end it."""
        sorted_chunks = sorted(chunk_events, key=lambda x: x.created_at)
        downloads = "".join(chunk.content for chunk in sorted_chunks if ChatService.is_table_download(chunk))
        answer_chunks = [chunk for chunk in sorted_chunks if not ChatService.is_table_download(chunk)]
        streamed = "".join(chunk.content for chunk in answer_chunks)
        chat_content = ChatContent(content=streamed, reasoning_content="")
        chat_content.reasoning_content = "".join(getattr(chunk, "reasoning_content", "") for chunk in sorted_chunks)
        if stop_event.is_hitl_request_event:
            chat_content.content += stop_event.question + downloads
            return chat_content
        full_answer = ChatService.terminal_output_text(getattr(stop_event, "output_messages", None))
        suffix = ChatService.missing_suffix(
            ChatService.answer_text([chunk.content for chunk in answer_chunks]), full_answer
        )
        chat_content.content = streamed + suffix + downloads
        return chat_content

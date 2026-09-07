import asyncio
import time
import uuid
from collections import Counter
from unittest.mock import patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from bson import ObjectId
from httpx import ASGITransport, AsyncClient, Response
from llama_index.core.base.llms.types import ChatMessage, MessageRole, TextBlock
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import ChunkEvent, ControlEvent, LLMStopEvent, Message, UserMessageEvent
from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import (
    PersistedAgentEventEntity,
)
from swiss_ai_hub.core.persistence.utils import str_to_object_id
from swiss_ai_hub.core.publishers import NCPublisher
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler, fake_user
from swiss_ai_hub.core.topic_managers import AgentThreadTopicManager, AgentTopicManager
from swiss_ai_hub.core.topics.agents import AgentInstanceTopic

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

BASE_URL = "http://test/api/v1/active"
COMPLETIONS_ENDPOINT = "/openai/chat/completions"

AGENT_CLASS = "history_agent"
AGENT_ID = "history_agent_1"
REPLY_TEXT = "Reply from the simulated agent"
RUNTIME_NESTED_PROMPT = "Seed a live nested AITL-shaped response"

PERSISTENCE_TIMEOUT_SECONDS = 10


class RecordingSimulatedAgentRunner(SimulatedAgentApiTestRunner):
    """Records the UserMessageEvents the simulated agent receives, so tests can assert on the
    message history the API reconstructed for the agent."""

    def __init__(self, agent_class: str, agent_id: str):
        super().__init__(agent_class=agent_class, agent_id=agent_id)
        self.received_user_message_events: list[UserMessageEvent] = []

    async def simulate_agent(self, event: ControlEvent, topic: AgentInstanceTopic):
        if isinstance(event, UserMessageEvent):
            self.received_user_message_events.append(event)
            if event.user_query == RUNTIME_NESTED_PROMPT:
                await self._publish_nested_runtime_events(topic)
                return
        await super().simulate_agent(event, topic)

    async def _publish_display_as(
        self,
        event: BaseEvent,
        topic: AgentInstanceTopic,
        *,
        agent_class: str,
        agent_id: str,
        display_id: str,
        run_id: str,
    ) -> None:
        assert self.nc is not None
        topic_manager = AgentThreadTopicManager(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=topic.thread_id,
            display_id=display_id,
            run_id=run_id,
        )
        subject = topic_manager.get_subject_for_display_event_in_thread(event.event_name, event.event_id)
        await NCPublisher("RuntimeNestedHistoryTest", self.nc).publish_event(event, subject)

    async def _publish_nested_runtime_events(self, topic: AgentInstanceTopic) -> None:
        hidden_display = str(ObjectId())
        primary_chunk = ChunkEvent(content="Primary ", model_name="sim")
        primary_chunk.event_id = "runtime-primary-chunk"
        shared_chunk = ChunkEvent(content="nested ", model_name="sim")
        shared_chunk.event_id = "runtime-shared-chunk"
        deep_chunk = ChunkEvent(content="deep ", model_name="sim")
        deep_chunk.event_id = "runtime-deep-chunk"
        hidden_chunk = ChunkEvent(content="HIDDEN", model_name="sim")
        hidden_chunk.event_id = "runtime-hidden-chunk"
        unknown_hidden = ControlAndDisplayEvent.deserialize_event(
            {
                "event_id": "runtime-hidden-aitl",
                "created_at": time.time_ns(),
                "_event_name": "RetrievalAgentInTheLoopResponseEvent",
                "_parent_event_names": [
                    "RetrievalAgentInTheLoopResponseEvent",
                    "AgentInTheLoopResponseEvent",
                    "ControlAndDisplayEvent",
                    "DisplayEvent",
                    "ControlEvent",
                ],
                "stop_event": {
                    "event_id": "runtime-hidden-retrieval-stop",
                    "created_at": time.time_ns(),
                    "_event_name": "RetrievalResponseEvent",
                    "_parent_event_names": [
                        "RetrievalResponseEvent",
                        "RetrieverEvent",
                        "SemanticEvent",
                        "StopEvent",
                        "ControlAndDisplayEvent",
                        "DisplayEvent",
                        "ControlEvent",
                    ],
                    "nodes": [],
                },
            }
        )
        primary_stop = LLMStopEvent(
            output_messages=[Message.from_string(role="assistant", content="Primary nested deep final")]
        )
        primary_stop.event_id = "runtime-primary-stop"

        await self._publish_display_as(
            primary_chunk,
            topic,
            agent_class=AGENT_CLASS,
            agent_id=AGENT_ID,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        await self._publish_display_as(
            shared_chunk,
            topic,
            agent_class="NestedAgent",
            agent_id="nested-shared",
            display_id=topic.display_id,
            run_id="runtime-nested-run",
        )
        await self._publish_display_as(
            deep_chunk,
            topic,
            agent_class="DeepNestedAgent",
            agent_id="nested-deep",
            display_id=topic.display_id,
            run_id="runtime-deep-run",
        )
        await self._publish_display_as(
            hidden_chunk,
            topic,
            agent_class="HiddenNestedAgent",
            agent_id="nested-hidden",
            display_id=hidden_display,
            run_id="runtime-hidden-run",
        )
        await self._publish_display_as(
            unknown_hidden,
            topic,
            agent_class="HiddenNestedAgent",
            agent_id="nested-hidden",
            display_id=hidden_display,
            run_id="runtime-hidden-run",
        )
        await self._publish_display_as(
            primary_stop,
            topic,
            agent_class=AGENT_CLASS,
            agent_id=AGENT_ID,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        assert self.nc is not None
        await self.nc.flush()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client_and_runner():
    auth = TestAuthHandler()
    controller = OpenaiController(auth=auth).chat_completion_with_assistants()

    runner = RecordingSimulatedAgentRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    runner.simulated_events = [
        ChunkEvent(content=REPLY_TEXT, model_name="sim"),
        LLMStopEvent(output_messages=[Message.from_string(role="assistant", content=REPLY_TEXT)]),
    ]

    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        runner.create_agent_config_in_db()
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client, runner


async def _completion(
    client: AsyncClient,
    thread_id: str,
    content: str,
    reconstruct_history: bool,
    *,
    display_id: str | None = None,
    stream: bool = False,
    send_display_id: bool = True,
) -> Response:
    metadata: dict[str, str | bool] = {"thread_id": thread_id}
    if send_display_id:
        metadata["display_id"] = display_id or str(ObjectId())
    if reconstruct_history:
        metadata["reconstruct_history"] = True
    response = await client.post(
        COMPLETIONS_ENDPOINT,
        json={
            "model": f"{AGENT_CLASS}/{AGENT_ID}",
            "messages": [{"role": "user", "content": content}],
            "stream": stream,
            "metadata": metadata,
        },
    )
    assert response.status_code == 200, f"Response: {response.text}"
    return response


async def _await_persisted_display_events(thread_id: str, event_names: set[str]) -> None:
    """Event persistence runs on a NATS subscriber outside the request lifecycle, so wait until the
    given event names are persisted for the thread before continuing."""
    deadline = time.monotonic() + PERSISTENCE_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        persisted = PersistedAgentEventEntity.display_events_for_thread(thread_id)
        if event_names <= {event.event_name for event in persisted}:
            return
        await asyncio.sleep(0.1)
    pytest.fail(f"Events {event_names} not persisted for thread {thread_id} within {PERSISTENCE_TIMEOUT_SECONDS}s")


async def _await_persisted_event_ids(thread_id: str, event_ids: set[str]) -> None:
    deadline = time.monotonic() + PERSISTENCE_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        persisted = PersistedAgentEventEntity.display_events_for_thread(thread_id)
        if event_ids <= {event.event_id for event in persisted}:
            return
        await asyncio.sleep(0.1)
    pytest.fail(f"Events {event_ids} not persisted for thread {thread_id} within {PERSISTENCE_TIMEOUT_SECONDS}s")


def _last_received_event(
    runner: RecordingSimulatedAgentRunner, start_index: int, expected_count: int
) -> UserMessageEvent:
    received_events = runner.received_user_message_events[start_index:]
    assert len(received_events) == expected_count
    return received_events[-1]


def _assert_messages(event: UserMessageEvent, expected: list[tuple[MessageRole, str]]) -> None:
    # These tests target identifier canonicalization: assert the complete message set without
    # coupling them to ThreadService's separate event-ordering contract.
    assert Counter((message.role, message.content) for message in event.messages) == Counter(expected)


@pytest.mark.asyncio(loop_scope="module")
async def test_reconstruct_history_with_non_object_id_thread_id(api_client_and_runner):
    """Regression test: a client thread id that is not a 24-hex ObjectID (e.g. a UUID) is
    canonicalized via str_to_object_id before events are persisted, so history reconstruction must
    query the canonicalized id. Otherwise the agent receives only the latest user message."""
    client, runner = api_client_and_runner
    thread_id = str(uuid.uuid4())
    start_index = len(runner.received_user_message_events)

    await _completion(client, thread_id, "First question", reconstruct_history=False)
    await _await_persisted_display_events(str(str_to_object_id(thread_id)), {"UserMessageEvent", "ChunkEvent"})
    await _completion(client, thread_id, "Second question", reconstruct_history=True)

    event = _last_received_event(runner, start_index, expected_count=2)
    _assert_messages(
        event,
        [
            (MessageRole.USER, "First question"),
            (MessageRole.ASSISTANT, REPLY_TEXT),
            (MessageRole.USER, "Second question"),
        ],
    )


@pytest.mark.parametrize(
    ("thread_id", "case_name"),
    [
        pytest.param("g" + uuid.uuid4().hex[:23], "24-character non-hex ID", id="24-character-non-hex"),
        pytest.param(("ABCDEF" + str(ObjectId())[6:]).upper(), "uppercase ObjectID", id="uppercase-object-id"),
        pytest.param(f"ext-{uuid.uuid4().hex[:8]}", "short external ID", id="short-external-id"),
    ],
)
@pytest.mark.asyncio(loop_scope="module")
async def test_reconstruct_history_with_adversarial_thread_id_formats(
    api_client_and_runner, thread_id: str, case_name: str
):
    """Canonicalization must be symmetric for valid and invalid ObjectID-shaped client identifiers."""
    client, runner = api_client_and_runner
    start_index = len(runner.received_user_message_events)
    first_message = f"First question for {case_name}"
    second_message = f"Second question for {case_name}"

    await _completion(client, thread_id, first_message, reconstruct_history=False)
    await _await_persisted_display_events(str(str_to_object_id(thread_id)), {"UserMessageEvent", "ChunkEvent"})
    await _completion(client, thread_id, second_message, reconstruct_history=True)

    event = _last_received_event(runner, start_index, expected_count=2)
    _assert_messages(
        event,
        [
            (MessageRole.USER, first_message),
            (MessageRole.ASSISTANT, REPLY_TEXT),
            (MessageRole.USER, second_message),
        ],
    )


@pytest.mark.asyncio(loop_scope="module")
async def test_reconstruct_history_on_new_thread_keeps_only_current_message(api_client_and_runner):
    """Requesting reconstruction for a thread with no persisted events must not invent history."""
    client, runner = api_client_and_runner
    start_index = len(runner.received_user_message_events)
    current_message = "Only message in a new thread"

    await _completion(client, str(uuid.uuid4()), current_message, reconstruct_history=True)

    event = _last_received_event(runner, start_index, expected_count=1)
    _assert_messages(event, [(MessageRole.USER, current_message)])


@pytest.mark.asyncio(loop_scope="module")
async def test_reconstruct_history_false_does_not_load_existing_history(api_client_and_runner):
    """Persisted history must remain opt-in even when the client reuses the same external thread ID."""
    client, runner = api_client_and_runner
    thread_id = str(uuid.uuid4())
    start_index = len(runner.received_user_message_events)

    await _completion(client, thread_id, "Prior message that must stay hidden", reconstruct_history=False)
    await _await_persisted_display_events(str(str_to_object_id(thread_id)), {"UserMessageEvent", "ChunkEvent"})
    with patch.object(PersistedAgentEventEntity, "conversation_events_for_thread") as history_query:
        await _completion(client, thread_id, "Current message without reconstruction", reconstruct_history=False)
    history_query.assert_not_called()

    event = _last_received_event(runner, start_index, expected_count=2)
    _assert_messages(event, [(MessageRole.USER, "Current message without reconstruction")])


@pytest.mark.asyncio(loop_scope="module")
async def test_reconstruct_history_does_not_leak_between_external_thread_ids(api_client_and_runner):
    """Different external IDs must remain isolated after deterministic ObjectID conversion."""
    client, runner = api_client_and_runner
    thread_a = str(uuid.uuid4())
    thread_b = str(uuid.uuid4())
    start_index = len(runner.received_user_message_events)

    await _completion(client, thread_a, "Thread A prior question", reconstruct_history=False)
    await _await_persisted_display_events(str(str_to_object_id(thread_a)), {"UserMessageEvent", "ChunkEvent"})
    await _completion(client, thread_b, "Thread B private question", reconstruct_history=False)
    await _await_persisted_display_events(str(str_to_object_id(thread_b)), {"UserMessageEvent", "ChunkEvent"})
    await _completion(client, thread_a, "Thread A follow-up", reconstruct_history=True)

    event = _last_received_event(runner, start_index, expected_count=3)
    _assert_messages(
        event,
        [
            (MessageRole.USER, "Thread A prior question"),
            (MessageRole.ASSISTANT, REPLY_TEXT),
            (MessageRole.USER, "Thread A follow-up"),
        ],
    )


def _save_persisted_event(
    *,
    thread_id: str,
    display_id: str,
    event_name: str,
    event_parents: list[str],
    event_data: dict,
    event_id: str,
    agent_class: str,
    agent_id: str,
    run_id: str,
) -> None:
    PersistedAgentEventEntity(
        agent_class=agent_class,
        agent_id=agent_id,
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
        event_id=event_id,
        event_type=AgentTopicManager.DISPLAY_EVENT,
        event_name=event_name,
        event_data=event_data,
        event_parents=event_parents,
    ).save()


def _seed_nested_history(thread_id: str) -> str:
    visible_display = str(ObjectId())
    hidden_display = str(ObjectId())
    user_event = UserMessageEvent(
        user=fake_user(),
        messages=[ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="Persisted visible question")])],
    )
    user_data = user_event.model_dump()
    user_data["created_at"] = 1
    _save_persisted_event(
        thread_id=thread_id,
        display_id=visible_display,
        event_name=user_event.event_name,
        event_parents=user_event._parent_event_names,
        event_data=user_data,
        event_id="visible-user",
        agent_class="UserAgent",
        agent_id=fake_user().id,
        run_id="top-level-run",
    )

    def save_chunk(
        content: str,
        *,
        event_id: str,
        created_at: int,
        display_id: str,
        agent_class: str,
        agent_id: str,
        run_id: str,
    ) -> None:
        chunk = ChunkEvent(content=content, model_name="sim")
        chunk_data = chunk.model_dump()
        chunk_data["created_at"] = created_at
        _save_persisted_event(
            thread_id=thread_id,
            display_id=display_id,
            event_name=chunk.event_name,
            event_parents=chunk._parent_event_names,
            event_data=chunk_data,
            event_id=event_id,
            agent_class=agent_class,
            agent_id=agent_id,
            run_id=run_id,
        )

    save_chunk(
        "Primary ",
        event_id="primary-chunk",
        created_at=2,
        display_id=visible_display,
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        run_id="top-level-run",
    )
    save_chunk(
        "delegated ",
        event_id="shared-nested-chunk",
        created_at=3,
        display_id=visible_display,
        agent_class="NestedAgent",
        agent_id="nested-shared",
        run_id="nested-shared-run",
    )
    save_chunk(
        "delegated ",
        event_id="shared-nested-chunk",
        created_at=3,
        display_id=visible_display,
        agent_class="NestedAgent",
        agent_id="nested-shared",
        run_id="nested-shared-run",
    )
    save_chunk(
        "HIDDEN",
        event_id="hidden-chunk",
        created_at=4,
        display_id=hidden_display,
        agent_class="NestedAgent",
        agent_id="nested-hidden",
        run_id="nested-hidden-run",
    )
    _save_persisted_event(
        thread_id=thread_id,
        display_id=hidden_display,
        event_name="RetrievalAgentInTheLoopResponseEvent",
        event_parents=["RetrievalAgentInTheLoopResponseEvent", "AgentInTheLoopResponseEvent"],
        event_data={
            "created_at": 5,
            "stop_event": {
                "_event_name": "RetrievalResponseEvent",
                "_parent_event_names": ["RetrievalResponseEvent", "RetrieverEvent", "StopEvent"],
                "nodes": [],
            },
        },
        event_id="unknown-hidden-aitl",
        agent_class="NestedAgent",
        agent_id="nested-hidden",
        run_id="nested-hidden-run",
    )
    stop = LLMStopEvent(output_messages=[Message.from_string(role="assistant", content="Primary delegated final")])
    stop_data = stop.model_dump()
    stop_data["created_at"] = 6
    _save_persisted_event(
        thread_id=thread_id,
        display_id=visible_display,
        event_name=stop.event_name,
        event_parents=stop._parent_event_names,
        event_data=stop_data,
        event_id="primary-stop",
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        run_id="top-level-run",
    )
    return visible_display


@pytest.mark.parametrize("stream", [False, True], ids=["json", "stream"])
@pytest.mark.asyncio(loop_scope="module")
async def test_nested_visibility_unknown_events_and_duplicates_end_to_end(api_client_and_runner, stream: bool):
    client, runner = api_client_and_runner
    external_thread_id = str(uuid.uuid4())
    thread_id = str(str_to_object_id(external_thread_id))
    visible_display = _seed_nested_history(thread_id)
    start_index = len(runner.received_user_message_events)

    first_read = await ThreadService.thread_as_message_history(
        thread_id,
        primary_agent_class=AGENT_CLASS,
        primary_agent_id=AGENT_ID,
    )
    second_read = await ThreadService.thread_as_message_history(
        thread_id,
        primary_agent_class=AGENT_CLASS,
        primary_agent_id=AGENT_ID,
    )
    assert first_read.model_dump_json() == second_read.model_dump_json()

    await _completion(
        client,
        external_thread_id,
        "Current follow-up",
        reconstruct_history=True,
        display_id=str(ObjectId()),
        stream=stream,
    )

    event = _last_received_event(runner, start_index, expected_count=1)
    _assert_messages(
        event,
        [
            (MessageRole.USER, "Persisted visible question"),
            (MessageRole.ASSISTANT, "Primary delegated final"),
            (MessageRole.USER, "Current follow-up"),
        ],
    )
    assert all("HIDDEN" not in (message.content or "") for message in event.messages)
    persisted = list(PersistedAgentEventEntity.display_events_for_thread(thread_id))
    assert sum(item.event_id == "unknown-hidden-aitl" for item in persisted) == 1
    assert sum(item.display_id == visible_display and item.event_id == "shared-nested-chunk" for item in persisted) == 2


@pytest.mark.asyncio(loop_scope="module")
async def test_live_nested_nats_flow_reconstructs_only_client_visible_history(api_client_and_runner):
    client, runner = api_client_and_runner
    external_thread_id = str(uuid.uuid4())
    thread_id = str(str_to_object_id(external_thread_id))
    start_index = len(runner.received_user_message_events)
    first_display = str(ObjectId())

    first_response = await _completion(
        client,
        external_thread_id,
        RUNTIME_NESTED_PROMPT,
        reconstruct_history=False,
        display_id=first_display,
    )
    assert first_response.json()["choices"][0]["message"]["content"] == "Primary nested deep final"
    await _await_persisted_event_ids(
        thread_id,
        {
            "runtime-primary-chunk",
            "runtime-shared-chunk",
            "runtime-deep-chunk",
            "runtime-hidden-chunk",
            "runtime-hidden-aitl",
            "runtime-primary-stop",
        },
    )

    await _completion(
        client,
        external_thread_id,
        "Follow-up after live nesting",
        reconstruct_history=True,
    )

    event = _last_received_event(runner, start_index, expected_count=2)
    _assert_messages(
        event,
        [
            (MessageRole.USER, RUNTIME_NESTED_PROMPT),
            (MessageRole.ASSISTANT, "Primary nested deep final"),
            (MessageRole.USER, "Follow-up after live nesting"),
        ],
    )
    assert all("HIDDEN" not in (message.content or "") for message in event.messages)
    persisted = list(PersistedAgentEventEntity.display_events_for_thread(thread_id))
    assert sum(item.event_id == "runtime-hidden-aitl" for item in persisted) == 1


@pytest.mark.parametrize("messages", [[], None], ids=["empty", "null"])
@pytest.mark.asyncio(loop_scope="module")
async def test_empty_messages_with_reconstruction_returns_http_400(api_client_and_runner, messages):
    client, runner = api_client_and_runner
    start_index = len(runner.received_user_message_events)

    response = await client.post(
        COMPLETIONS_ENDPOINT,
        json={
            "model": f"{AGENT_CLASS}/{AGENT_ID}",
            "messages": messages,
            "stream": False,
            "metadata": {
                "thread_id": str(uuid.uuid4()),
                "reconstruct_history": True,
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "At least one message is required when reconstruct_history is enabled."
    assert len(runner.received_user_message_events) == start_index


@pytest.mark.asyncio(loop_scope="module")
async def test_openwebui_shaped_request_passes_client_history_through_untouched(api_client_and_runner):
    """The OpenWebUI pipeline sends the full client-managed message list with thread/display ids and
    no reconstruct_history flag. The API must pass those messages through exactly as sent."""
    client, runner = api_client_and_runner
    thread_id = str(ObjectId())
    start_index = len(runner.received_user_message_events)

    client_messages = [
        {"role": "user", "content": "Client-managed first question"},
        {"role": "assistant", "content": "Client-managed first answer"},
        {"role": "user", "content": "Client-managed second question"},
    ]
    with patch.object(PersistedAgentEventEntity, "conversation_events_for_thread") as history_query:
        response = await client.post(
            COMPLETIONS_ENDPOINT,
            json={
                "model": f"{AGENT_CLASS}/{AGENT_ID}",
                "messages": client_messages,
                "stream": False,
                "metadata": {"thread_id": thread_id, "display_id": str(ObjectId())},
            },
        )

    assert response.status_code == 200, f"Response: {response.text}"
    history_query.assert_not_called()
    event = _last_received_event(runner, start_index, expected_count=1)
    assert [(message.role, message.content) for message in event.messages] == [
        (MessageRole.USER, "Client-managed first question"),
        (MessageRole.ASSISTANT, "Client-managed first answer"),
        (MessageRole.USER, "Client-managed second question"),
    ]


@pytest.mark.asyncio(loop_scope="module")
async def test_web_chat_shaped_request_reconstructs_without_client_display_id(api_client_and_runner):
    """The web chat composable sends only the latest message with a canonical thread id and
    reconstruct_history=true, omitting display_id entirely. Every per-run display the API
    generates must remain visible to reconstruction."""
    client, runner = api_client_and_runner
    thread_id = str(ObjectId())
    start_index = len(runner.received_user_message_events)

    await _completion(client, thread_id, "First web chat question", reconstruct_history=False, send_display_id=False)
    await _await_persisted_display_events(thread_id, {"UserMessageEvent", "ChunkEvent"})
    await _completion(client, thread_id, "Second web chat question", reconstruct_history=True, send_display_id=False)

    event = _last_received_event(runner, start_index, expected_count=2)
    _assert_messages(
        event,
        [
            (MessageRole.USER, "First web chat question"),
            (MessageRole.ASSISTANT, REPLY_TEXT),
            (MessageRole.USER, "Second web chat question"),
        ],
    )

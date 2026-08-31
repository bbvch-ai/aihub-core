import logging
from collections.abc import Iterable
from typing import Any
from unittest.mock import patch

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import AudioBlock, ChatMessage, ImageBlock, MessageRole, TextBlock
from openai.types.chat import ChatCompletionMessageParam
from swiss_ai_hub.core.events.agent import ChunkEvent, Message, UserMessageEvent
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import (
    PersistedAgentEventEntity,
)
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topic_managers import AgentTopicManager

from swiss_ai_hub.api.routes.thread.conversation_history_projector import project_conversation_history
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService

THREAD_ID = str(ObjectId())
VISIBLE_DISPLAY = str(ObjectId())
HIDDEN_DISPLAY = str(ObjectId())
PRIMARY_CLASS = "PrimaryAgent"
PRIMARY_ID = "primary"
PROJECTOR_LOGGER = "swiss_ai_hub.api.routes.thread.conversation_history_projector"


def _raw_event(
    *,
    event_name: str,
    parents: list[str],
    created_at: int,
    event_id: str,
    agent_class: str = PRIMARY_CLASS,
    agent_id: str = PRIMARY_ID,
    display_id: str = VISIBLE_DISPLAY,
    run_id: str = "run-1",
    event_data: dict[str, Any] | None = None,
) -> PersistedAgentEventEntity:
    return PersistedAgentEventEntity(
        agent_class=agent_class,
        agent_id=agent_id,
        thread_id=THREAD_ID,
        display_id=display_id,
        run_id=run_id,
        event_id=event_id,
        event_type=AgentTopicManager.DISPLAY_EVENT,
        event_name=event_name,
        event_data={"created_at": created_at, **(event_data or {})},
        event_parents=parents,
    )


def _persisted_event(
    event,
    *,
    created_at: int,
    event_id: str,
    agent_class: str = PRIMARY_CLASS,
    agent_id: str = PRIMARY_ID,
    display_id: str = VISIBLE_DISPLAY,
    run_id: str = "run-1",
) -> PersistedAgentEventEntity:
    event_data = event.model_dump()
    event_data["created_at"] = created_at
    return _raw_event(
        event_name=event.event_name,
        parents=event._parent_event_names,
        created_at=created_at,
        event_id=event_id,
        agent_class=agent_class,
        agent_id=agent_id,
        display_id=display_id,
        run_id=run_id,
        event_data=event_data,
    )


def _user(
    text: str,
    *,
    created_at: int,
    event_id: str,
    display_id: str = VISIBLE_DISPLAY,
    messages: list[ChatMessage] | None = None,
) -> PersistedAgentEventEntity:
    user_messages = messages or [ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text=text)])]
    return _persisted_event(
        UserMessageEvent(user=fake_user(), messages=user_messages),
        created_at=created_at,
        event_id=event_id,
        agent_class="UserAgent",
        agent_id=fake_user().id,
        display_id=display_id,
    )


def _empty_user(*, created_at: int, event_id: str) -> PersistedAgentEventEntity:
    return _persisted_event(
        UserMessageEvent(user=fake_user(), messages=[]),
        created_at=created_at,
        event_id=event_id,
        agent_class="UserAgent",
        agent_id=fake_user().id,
    )


def _chunk(
    text: str,
    *,
    created_at: int,
    event_id: str,
    agent_class: str = PRIMARY_CLASS,
    agent_id: str = PRIMARY_ID,
    display_id: str = VISIBLE_DISPLAY,
    run_id: str = "run-1",
) -> PersistedAgentEventEntity:
    return _persisted_event(
        ChunkEvent(content=text, model_name="sim"),
        created_at=created_at,
        event_id=event_id,
        agent_class=agent_class,
        agent_id=agent_id,
        display_id=display_id,
        run_id=run_id,
    )


def _hitl_request(
    question: Any,
    *,
    created_at: int,
    event_id: str,
    display_id: str = VISIBLE_DISPLAY,
) -> PersistedAgentEventEntity:
    return _raw_event(
        event_name="CustomHumanInTheLoopRequestEvent",
        parents=["CustomHumanInTheLoopRequestEvent", "HumanInTheLoopRequestEvent"],
        created_at=created_at,
        event_id=event_id,
        display_id=display_id,
        event_data={"question": question},
    )


def _hitl_response(
    response: Any,
    *,
    created_at: int,
    event_id: str,
    display_id: str = VISIBLE_DISPLAY,
    request_event: Any = None,
) -> PersistedAgentEventEntity:
    return _raw_event(
        event_name="CustomHumanInTheLoopResponseEvent",
        parents=["CustomHumanInTheLoopResponseEvent", "HumanInTheLoopResponseEvent"],
        created_at=created_at,
        event_id=event_id,
        agent_class="UserAgent",
        agent_id=fake_user().id,
        display_id=display_id,
        event_data={"response": response, "request_event": request_event},
    )


def _stop(
    full_answer: Any,
    *,
    created_at: int,
    event_id: str,
    agent_class: str = PRIMARY_CLASS,
    agent_id: str = PRIMARY_ID,
    display_id: str = VISIBLE_DISPLAY,
) -> PersistedAgentEventEntity:
    output_messages = (
        [Message.from_string(role="assistant", content=full_answer).model_dump()]
        if isinstance(full_answer, str)
        else full_answer
    )
    return _raw_event(
        event_name="CustomStopEvent",
        parents=["CustomStopEvent", "StopEvent"],
        created_at=created_at,
        event_id=event_id,
        agent_class=agent_class,
        agent_id=agent_id,
        display_id=display_id,
        event_data={"output_messages": output_messages},
    )


def _project(
    events: Iterable[PersistedAgentEventEntity],
    *,
    primary_agent_class: str | None = PRIMARY_CLASS,
    primary_agent_id: str | None = PRIMARY_ID,
) -> list[ChatCompletionMessageParam]:
    return project_conversation_history(
        events,
        primary_agent_class=primary_agent_class,
        primary_agent_id=primary_agent_id,
    )


def _text(role: str, content: str) -> dict[str, Any]:
    return {"role": role, "content": [{"type": "text", "text": content}]}


def test_existing_non_nested_conversation_order_is_preserved():
    events = [
        _user("question one", created_at=1, event_id="u1"),
        _chunk("Hel", created_at=2, event_id="c1"),
        _chunk("lo", created_at=3, event_id="c2"),
        _user("question two", created_at=4, event_id="u2"),
        _chunk("Next answer", created_at=5, event_id="c3"),
    ]

    assert _project(events) == [
        _text("user", "question one"),
        _text("assistant", "Hello"),
        _text("user", "question two"),
        _text("assistant", "Next answer"),
    ]


def test_multimodal_user_input_uses_last_message_and_normalizes_legacy_audio():
    stale = ChatMessage(role=MessageRole.USER, blocks=[TextBlock(text="stale")])
    latest = ChatMessage(
        role=MessageRole.USER,
        blocks=[
            TextBlock(text="latest"),
            ImageBlock(url="https://example.com/image.png"),
            AudioBlock(audio=b"encoded-audio", format="wav"),
        ],
    )
    event = _user("", created_at=1, event_id="u1", messages=[stale, latest])

    assert _project([event]) == [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "latest"},
                {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}},
                {
                    "type": "input_audio",
                    "input_audio": {"data": "ZW5jb2RlZC1hdWRpbw==", "format": "wav"},
                },
            ],
        }
    ]


def test_empty_user_event_is_skipped_with_metadata_only_warning(caplog):
    event = _empty_user(created_at=1, event_id="empty-user")

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        assert _project([event]) == []

    record = caplog.records[-1]
    assert record.message == "Skipping malformed visible history event"
    assert record.event_id == "empty-user"
    assert record.error_type == "ValueError"
    assert "messages" not in record.getMessage()


def test_unrelated_visible_event_is_ignored_without_payload_access(caplog):
    marker = _user("question", created_at=1, event_id="u1")
    unrelated = _raw_event(
        event_name="RetrievalAgentInTheLoopResponseEvent",
        parents=["RetrievalAgentInTheLoopResponseEvent", "AgentInTheLoopResponseEvent"],
        created_at=2,
        event_id="aitl",
        event_data={"secret": "must-not-be-read", "created_at": "malformed-but-unread"},
    )

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        assert _project([marker, unrelated]) == [_text("user", "question")]

    assert not caplog.records


def test_malformed_relevant_event_is_skipped_and_later_event_survives(caplog):
    marker = _user("question", created_at=1, event_id="u1")
    malformed = _raw_event(
        event_name="ChunkEvent",
        parents=["ChunkEvent"],
        created_at=2,
        event_id="bad-chunk",
        event_data={"content": 12345},
    )
    valid = _chunk("valid answer", created_at=3, event_id="good-chunk")

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        messages = _project([marker, malformed, valid])

    assert messages == [_text("user", "question"), _text("assistant", "valid answer")]
    assert caplog.records[-1].event_id == "bad-chunk"
    assert caplog.records[-1].error_type == "ValueError"


def test_invalid_order_metadata_is_skipped_before_sorting(caplog):
    marker = _user("question", created_at=1, event_id="u1")
    malformed_order = _raw_event(
        event_name="ChunkEvent",
        parents=["ChunkEvent"],
        created_at=2,
        event_id="bad-order",
        event_data={"created_at": "not-an-integer", "content": "must not project"},
    )
    valid = _chunk("valid answer", created_at=3, event_id="good-chunk")

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        messages = _project([marker, malformed_order, valid])

    assert messages == [_text("user", "question"), _text("assistant", "valid answer")]
    assert caplog.records[-1].event_id == "bad-order"
    assert caplog.records[-1].error_type == "TypeError"


def test_replica_delivery_duplicates_contribute_once():
    marker = _user("question", created_at=1, event_id="u1")
    chunk = _chunk("answer", created_at=2, event_id="c1")

    assert _project([marker, marker, chunk, chunk, chunk]) == [
        _text("user", "question"),
        _text("assistant", "answer"),
    ]


def test_equal_created_at_is_ordered_by_event_id():
    marker = _user("question", created_at=1, event_id="u1")
    first = _chunk("A", created_at=2, event_id="a")
    second = _chunk("B", created_at=2, event_id="b")

    assert _project([marker, second, first]) == [
        _text("user", "question"),
        _text("assistant", "AB"),
    ]


def test_three_level_shared_display_includes_all_agent_chunks():
    events = [
        _user("question", created_at=1, event_id="u1"),
        _chunk("A", created_at=2, event_id="a", agent_class="AgentA", agent_id="a"),
        _chunk("B", created_at=3, event_id="b", agent_class="AgentB", agent_id="b"),
        _chunk("C", created_at=4, event_id="c", agent_class="AgentC", agent_id="c"),
    ]

    assert _project(events) == [_text("user", "question"), _text("assistant", "ABC")]


def test_hidden_nested_subtree_is_excluded_before_payload_access(caplog):
    events = [
        _user("question", created_at=1, event_id="u1"),
        _chunk("visible", created_at=2, event_id="a"),
        _chunk("hidden B", created_at=3, event_id="b", display_id=HIDDEN_DISPLAY),
        _raw_event(
            event_name="UnknownNestedRetrievalEvent",
            parents=["UnknownNestedRetrievalEvent", "ChunkEvent"],
            created_at=4,
            event_id="c",
            agent_class="AgentC",
            agent_id="c",
            display_id=HIDDEN_DISPLAY,
            event_data={"content": {"malformed": "hidden"}},
        ),
    ]

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        assert _project(events) == [_text("user", "question"), _text("assistant", "visible")]

    assert not caplog.records


def test_mixed_visible_hidden_nesting_includes_visible_before_and_after():
    events = [
        _user("question", created_at=1, event_id="u1"),
        _chunk("A", created_at=2, event_id="a", agent_class="AgentA", agent_id="a"),
        _chunk("hidden", created_at=3, event_id="c", display_id=HIDDEN_DISPLAY),
        _chunk("B", created_at=4, event_id="b", agent_class="AgentB", agent_id="b"),
    ]

    assert _project(events) == [_text("user", "question"), _text("assistant", "AB")]


def test_recursive_same_agent_delegation_uses_display_not_identity_or_run():
    events = [
        _user("question", created_at=1, event_id="u1"),
        _chunk("outer", created_at=2, event_id="a", run_id="outer-run"),
        _chunk("inner", created_at=3, event_id="b", run_id="inner-run"),
        _chunk("resumed", created_at=4, event_id="c", run_id="outer-run"),
    ]

    assert _project(events) == [_text("user", "question"), _text("assistant", "outerinnerresumed")]


def test_nested_stop_on_visible_display_cannot_supply_primary_fallback():
    events = [
        _user("question", created_at=1, event_id="u1"),
        _chunk("stream", created_at=2, event_id="c1"),
        _stop(
            "stream nested secret",
            created_at=3,
            event_id="nested-stop",
            agent_class="NestedAgent",
            agent_id="nested",
        ),
        _stop("stream final", created_at=4, event_id="primary-stop"),
    ]

    assert _project(events) == [_text("user", "question"), _text("assistant", "stream final")]


def test_visible_delegated_chunk_from_other_agent_is_included():
    events = [
        _user("question", created_at=1, event_id="u1"),
        _chunk("delegated answer", created_at=2, event_id="worker", agent_class="Worker", agent_id="worker"),
    ]

    assert _project(events) == [_text("user", "question"), _text("assistant", "delegated answer")]


def test_hitl_request_projects_assistant_question():
    events = [
        _user("initial", created_at=1, event_id="u1"),
        _hitl_request("Please clarify", created_at=2, event_id="request"),
    ]

    assert _project(events) == [_text("user", "initial"), _text("assistant", "Please clarify")]


def test_hitl_response_projects_user_answer_once():
    response = _hitl_response("Human answer", created_at=1, event_id="response")

    assert _project([response]) == [_text("user", "Human answer")]


def test_boolean_hitl_confirmation_projects_as_text():
    confirmed = _hitl_response(True, created_at=1, event_id="confirmed")
    rejected = _hitl_response(False, created_at=2, event_id="rejected")

    assert _project([rejected]) == [_text("user", "false")]
    assert _project([confirmed]) == [_text("user", "true")]


def test_unsupported_audio_format_warns_and_keeps_representable_parts(caplog):
    latest = ChatMessage(
        role=MessageRole.USER,
        blocks=[
            TextBlock(text="see attached"),
            AudioBlock(audio=b"legacy", format="ogg"),
        ],
    )
    event = _user("", created_at=1, event_id="u1", messages=[latest])

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        messages = _project([event])

    assert messages == [_text("user", "see attached")]
    record = caplog.records[-1]
    assert record.message == "Skipping visible history audio block with unsupported format"
    assert record.event_id == "u1"
    assert record.audio_format == "ogg"


def test_boolean_audio_payload_is_rejected_as_malformed(caplog):
    event = _raw_event(
        event_name="UserMessageEvent",
        parents=["UserMessageEvent", "StartEvent"],
        created_at=1,
        event_id="bool-audio",
        agent_class="UserAgent",
        agent_id=fake_user().id,
        event_data={
            "messages": [
                {
                    "role": "user",
                    "blocks": [{"block_type": "audio", "audio": [True, False], "format": "wav"}],
                }
            ]
        },
    )

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        assert _project([event]) == []

    assert caplog.records[-1].event_id == "bool-audio"
    assert caplog.records[-1].error_type == "ValidationError"


def test_resumed_chunks_form_following_assistant_turn():
    events = [
        _user("initial", created_at=1, event_id="u1"),
        _hitl_request("Please clarify", created_at=2, event_id="request"),
        _hitl_response("Human answer", created_at=3, event_id="response"),
        _chunk("Resumed answer", created_at=4, event_id="chunk"),
    ]

    assert _project(events) == [
        _text("user", "initial"),
        _text("assistant", "Please clarify"),
        _text("user", "Human answer"),
        _text("assistant", "Resumed answer"),
    ]


def test_hitl_response_ignores_malformed_nested_request_when_response_is_valid():
    response = _hitl_response(
        "Human answer",
        created_at=1,
        event_id="response",
        request_event={"unknown_custom_event": object()},
    )

    assert _project([response]) == [_text("user", "Human answer")]


def test_hidden_hitl_is_excluded_until_user_marker_makes_display_visible():
    initial = _user("initial", created_at=1, event_id="u1")
    hidden_request = _hitl_request(
        "Hidden question",
        created_at=2,
        event_id="request",
        display_id=HIDDEN_DISPLAY,
    )

    assert _project([initial, hidden_request]) == [_text("user", "initial")]

    hidden_response = _hitl_response(
        "Visible answer",
        created_at=3,
        event_id="response",
        display_id=HIDDEN_DISPLAY,
    )
    assert _project([initial, hidden_request, hidden_response]) == [
        _text("user", "initial"),
        _text("assistant", "Hidden question"),
        _text("user", "Visible answer"),
    ]


@pytest.mark.parametrize(
    ("chunks", "full_answer", "expected"),
    [
        pytest.param([], "full answer", "full answer", id="no-chunks"),
        pytest.param(["partial "], "partial answer", "partial answer", id="partial-prefix"),
        pytest.param(["complete answer"], "complete answer", "complete answer", id="complete"),
        pytest.param(["divergent"], "different answer", "divergent", id="divergent"),
    ],
)
def test_primary_terminal_fallback_matches_live_prefix_rule(chunks: list[str], full_answer: str, expected: str):
    events: list[PersistedAgentEventEntity] = [_user("question", created_at=1, event_id="u1")]
    events.extend(_chunk(chunk, created_at=index + 2, event_id=f"c{index}") for index, chunk in enumerate(chunks))
    events.append(_stop(full_answer, created_at=len(chunks) + 2, event_id="stop"))

    assert _project(events) == [_text("user", "question"), _text("assistant", expected)]


def test_malformed_primary_stop_preserves_valid_chunks_and_warns(caplog):
    events = [
        _user("question", created_at=1, event_id="u1"),
        _chunk("streamed", created_at=2, event_id="chunk"),
        _stop([{"role": "assistant", "contents": "invalid"}], created_at=3, event_id="bad-stop"),
    ]

    with caplog.at_level(logging.WARNING, logger=PROJECTOR_LOGGER):
        messages = _project(events)

    assert messages == [_text("user", "question"), _text("assistant", "streamed")]
    assert caplog.records[-1].event_id == "bad-stop"
    assert caplog.records[-1].error_type == "ValidationError"


@pytest.mark.asyncio
async def test_thread_service_preserves_optional_primary_identity_contract():
    events = [_user("question", created_at=1, event_id="u1")]
    expected = [_text("user", "question")]
    with (
        patch.object(PersistedAgentEventEntity, "conversation_events_for_thread", return_value=events) as query,
        patch(
            "swiss_ai_hub.api.routes.thread.thread_service.project_conversation_history",
            return_value=expected,
        ) as projector,
    ):
        response = await ThreadService.thread_as_message_history(THREAD_ID)

    query.assert_called_once_with(THREAD_ID)
    projector.assert_called_once_with(events, primary_agent_class=None, primary_agent_id=None)
    assert response.messages[0]["role"] == "user"
    assert list(response.messages[0]["content"]) == expected[0]["content"]

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.distributor.external_agent_event_distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.tool_loop.tool_approval_request_event import ToolApprovalRequestEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_approval_response_event import ToolApprovalResponseEvent
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic

AGENT_X = AgentInstanceRef(agent_class="AgentX", agent_id="agent-x")
AGENT_Y = AgentInstanceRef(agent_class="AgentY", agent_id="agent-y")


class _CapturingPublisher:
    def __init__(self) -> None:
        self.subjects: list[str] = []

    async def publish_event(self, event, subject, extra_headers=None) -> None:
        self.subjects.append(subject)


def _distributor_with_capture() -> tuple[ExternalAgentEventDistributor, _CapturingPublisher]:
    distributor = ExternalAgentEventDistributor.__new__(ExternalAgentEventDistributor)
    publisher = _CapturingPublisher()
    distributor.js_publisher = publisher
    return distributor, publisher


def _start_external_event() -> ExternalAgentEvent:
    return ExternalAgentEvent(
        thread_id=str(ObjectId()),
        display_id=str(ObjectId()),
        event=UserMessageEvent(
            user=fake_user(),
            messages=[ChatMessage(role=MessageRole.USER, content="hi")],
        ),
    )


@pytest.mark.asyncio
async def test_target_agent_dispatches_only_to_selected_agent():
    distributor, publisher = _distributor_with_capture()
    thread = SimpleNamespace(id=ObjectId(), agents=[AGENT_X, AGENT_Y])
    external_event = _start_external_event()

    await distributor._handle_start_event(thread, external_event, run_id=str(ObjectId()), target_agent=AGENT_Y)

    assert len(publisher.subjects) == 1
    assert publisher.subjects[0].startswith(f"agent.{AGENT_Y.agent_class}.{AGENT_Y.agent_id}.")
    assert AGENT_X.agent_class not in publisher.subjects[0]


@pytest.mark.asyncio
async def test_no_target_agent_falls_back_to_all_thread_agents():
    distributor, publisher = _distributor_with_capture()
    thread = SimpleNamespace(id=ObjectId(), agents=[AGENT_X, AGENT_Y])
    external_event = _start_external_event()

    await distributor._handle_start_event(thread, external_event, run_id=str(ObjectId()), target_agent=None)

    assert len(publisher.subjects) == 2
    dispatched = {subject.split(".")[1] for subject in publisher.subjects}
    assert dispatched == {AGENT_X.agent_class, AGENT_Y.agent_class}


def _approval(thread_id: str, responded_by: str | None = None) -> ExternalAgentEvent:
    request = ToolApprovalRequestEvent(
        question="Allow?",
        topic=AgentInstanceTopic(
            agent_class=AGENT_X.agent_class,
            agent_id=AGENT_X.agent_id,
            thread_id=thread_id,
            display_id=str(ObjectId()),
            run_id=str(ObjectId()),
            event_type="control_event",
            event_name="ToolApprovalResponseEvent",
            event_id=str(ObjectId()),
        ),
        tool_call_id="c1",
        name="run_command",
        kind="function",
    )
    return ExternalAgentEvent(
        thread_id=thread_id,
        display_id=str(ObjectId()),
        event=ToolApprovalResponseEvent(response=True, request_event=request, responded_by=responded_by),
    )


def _thread_of(user_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=ObjectId(), agents=[AGENT_X], users=[SimpleNamespace(user_id=user_id)])


def _capturing_distributor() -> tuple[ExternalAgentEventDistributor, _CapturingPublisher]:
    distributor, publisher = _distributor_with_capture()
    distributor.nc_publisher = _CapturingPublisher()
    return distributor, publisher


@pytest.mark.asyncio
async def test_a_response_carries_its_authenticated_sender_not_the_one_the_client_names():
    distributor, publisher = _capturing_distributor()
    user = fake_user()
    thread = _thread_of(user.id)
    external_event = _approval(str(thread.id), responded_by="someone-else")

    with patch.object(ThreadEntity, "get_thread_by_id", return_value=thread):
        await distributor.distribute_event(external_event, user)

    assert external_event.event.responded_by == user.id
    assert len(publisher.subjects) == 1


@pytest.mark.asyncio
async def test_a_response_to_a_request_of_another_thread_is_refused():
    distributor, publisher = _capturing_distributor()
    user = fake_user()
    thread = _thread_of(user.id)
    external_event = _approval(str(ObjectId()))

    with patch.object(ThreadEntity, "get_thread_by_id", return_value=thread), pytest.raises(PermissionError):
        await distributor.distribute_event(external_event, user)

    assert publisher.subjects == []

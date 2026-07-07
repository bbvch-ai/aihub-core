from types import SimpleNamespace

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.distributor.external_agent_event_distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

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

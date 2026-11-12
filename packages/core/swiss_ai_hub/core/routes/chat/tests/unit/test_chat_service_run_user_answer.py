"""Another thread member's answer to a run's question is refused with a 403 before a subscriber is started."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from fastapi import HTTPException

from swiss_ai_hub.core.distributor.events.external_agent_event import ExternalAgentEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_approval_request_event import ToolApprovalRequestEvent
from swiss_ai_hub.core.events.agent.tool_loop.tool_approval_response_event import ToolApprovalResponseEvent
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import PersistedAgentEventEntity
from swiss_ai_hub.core.routes.chat.chat_service import ChatService
from swiss_ai_hub.core.subscribers.agent.agent_nc_subscriber import AgentNCSubscriber
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic


def _approval() -> ExternalAgentEvent:
    thread_id = str(ObjectId())
    request = ToolApprovalRequestEvent(
        question="Allow?",
        topic=AgentInstanceTopic(
            agent_class="UniversalAgent",
            agent_id="assistant",
            thread_id=thread_id,
            display_id=str(ObjectId()),
            run_id=str(ObjectId()),
            event_type=AgentTopicManager.CONTROL_EVENT,
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
        event=ToolApprovalResponseEvent(response=True, request_event=request),
    )


@pytest.mark.asyncio
async def test_an_answer_from_a_member_who_did_not_start_the_run_is_a_403_without_a_subscriber():
    distributor = MagicMock(distribute_event=AsyncMock())

    with (
        patch.object(PersistedAgentEventEntity, "user_id_of_run", return_value="run-owner"),
        patch.object(AgentNCSubscriber, "for_thread_display_events") as for_thread,
        pytest.raises(HTTPException) as refused,
    ):
        await ChatService.start_json_event_interaction(
            fake_user(), "UniversalAgent", "assistant", _approval(), MagicMock(), MagicMock(), distributor
        )

    assert refused.value.status_code == 403
    assert "started this run" in refused.value.detail
    for_thread.assert_not_called()
    distributor.distribute_event.assert_not_called()


def test_the_run_owner_answer_passes():
    owner = fake_user()

    with patch.object(PersistedAgentEventEntity, "user_id_of_run", return_value=owner.id):
        ChatService.ensure_answered_by_run_user(_approval(), owner)

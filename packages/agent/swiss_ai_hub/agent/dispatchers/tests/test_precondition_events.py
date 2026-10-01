"""A precondition may read events its step does not take; the dispatcher loads them too, without letting them
trigger the step."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from swiss_ai_hub.core.events.agent import ToolLoopIterationEvent, ToolResultEvent

from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher


@pytest.mark.asyncio
async def test_the_events_a_precondition_reads_are_loaded_for_it():
    dispatcher = AgentDispatcher.__new__(AgentDispatcher)
    dispatcher.agent = MagicMock(get_steps_waiting_for_event=MagicMock(return_value=[ToolLoop.join_step]))
    dispatcher.event_store = MagicMock(get_events_of_multiple_types=AsyncMock(return_value={}))
    dispatcher.is_step_ready = AsyncMock(return_value=False)
    event = ToolResultEvent(tool_call_id="c1", name="echo", content="done")

    await dispatcher._trigger_ready_steps(event, MagicMock(), MagicMock(), MagicMock(execution_context_id="r1"), MagicMock())

    loaded = dispatcher.event_store.get_events_of_multiple_types.await_args.args[1]
    assert ToolLoopIterationEvent.event_name_from_class() in loaded
    assert ToolResultEvent.event_name_from_class() in loaded

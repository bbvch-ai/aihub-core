"""The writer extracts on the originating agent's memory model (issue #1590).

The writer runs in its own execution context and cannot read the originating run's config, so the model
travels on the start event beside the rest of the origin identity. Without this, turning on asynchronous
storage would silently move extraction back to the platform default — the same profile would use a different
model depending on a checkbox that is about *when* the write happens, not *how*.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import StoreUserMemoryRequestedEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.memory_writer_agent.memory_writer_agent import MemoryWriterAgent

MEMORY_MODEL = "text-generation/memory-model"


def _request(origin_memory_llm: str | None) -> StoreUserMemoryRequestedEvent:
    return StoreUserMemoryRequestedEvent(
        user=fake_user(),
        messages=[ChatMessage(role=MessageRole.USER, content="remember I like dark mode")],
        locale="en",
        origin_thread_id="t1",
        origin_display_id="d1",
        origin_run_id="r1",
        origin_agent_class="RAGAgent",
        origin_agent_id="hr",
        origin_agent_name=LocaleString(en="HR"),
        origin_agent_description=LocaleString(en="HR agent"),
        origin_memory_llm=origin_memory_llm,
    )


async def _run_store_step(origin_memory_llm: str | None, extracted_by: str | None):
    """Run the step against a stubbed `AgentMemory`, returning the constructor kwargs and the stop event."""
    memory = MagicMock()
    memory.add_user_memory = AsyncMock(
        return_value=MagicMock(
            results=[],
            relations=MagicMock(added_entities=[], deleted_entities=[]),
            llm_model_name=extracted_by,
        )
    )
    target = "swiss_ai_hub.agent.agents.memory_writer_agent.memory_writer_agent.AgentMemory"
    with patch(target, return_value=memory) as agent_memory_cls:
        stop_event = await MemoryWriterAgent().store_step(_request(origin_memory_llm), t=MagicMock())
    return agent_memory_cls.call_args.kwargs, stop_event


@pytest.mark.asyncio
async def test_store_step_uses_the_origin_agents_memory_model():
    kwargs, _ = await _run_store_step(MEMORY_MODEL, extracted_by=MEMORY_MODEL)

    assert kwargs["llm_model_name"] == MEMORY_MODEL


@pytest.mark.asyncio
async def test_store_step_falls_back_to_the_platform_default():
    """An origin agent with no memory model configured leaves the writer on the platform default."""
    kwargs, _ = await _run_store_step(None, extracted_by="text-generation/platform-default")

    assert kwargs["llm_model_name"] is None


@pytest.mark.asyncio
async def test_the_stop_event_reports_the_model_that_extracted():
    """The writer run is traced on its own, so its terminal event is the only place the model can surface."""
    _, stop_event = await _run_store_step(MEMORY_MODEL, extracted_by=MEMORY_MODEL)

    assert stop_event.llm_model_name == MEMORY_MODEL

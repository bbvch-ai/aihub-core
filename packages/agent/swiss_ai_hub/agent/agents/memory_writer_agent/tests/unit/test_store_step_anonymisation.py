"""The writer anonymises the extraction of a memory that an anonymised run asked it to store."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import StoreUserMemoryRequestedEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.memory_writer_agent.memory_writer_agent import MemoryWriterAgent


async def _origin_config_of_a_write(origin_anonymise: bool):
    request = StoreUserMemoryRequestedEvent(
        user=fake_user(),
        messages=[ChatMessage(role=MessageRole.USER, content="Ich heisse Reto Wyss")],
        locale="de",
        origin_thread_id="t1",
        origin_display_id="d1",
        origin_run_id="r1",
        origin_agent_class="LLMWrappingAgent",
        origin_agent_id="hr",
        origin_agent_name=LocaleString(en="HR"),
        origin_agent_description=LocaleString(en="HR agent"),
        origin_anonymise=origin_anonymise,
    )
    memory = MagicMock()
    memory.add_user_memory = AsyncMock(
        return_value=MagicMock(
            results=[], relations=MagicMock(added_entities=[], deleted_entities=[]), llm_model_name=None
        )
    )
    target = "swiss_ai_hub.agent.agents.memory_writer_agent.memory_writer_agent.AgentMemory"
    with patch(target, return_value=memory) as agent_memory_cls:
        await MemoryWriterAgent().store_step(request, t=MagicMock())
    return agent_memory_cls.call_args.kwargs["agent_config"]


@pytest.mark.asyncio
async def test_should_anonymise_the_extraction_of_a_write_from_an_anonymised_run():
    assert (await _origin_config_of_a_write(origin_anonymise=True)).anonymise is True


@pytest.mark.asyncio
async def test_should_leave_other_writes_as_they_are():
    assert (await _origin_config_of_a_write(origin_anonymise=False)).anonymise is False

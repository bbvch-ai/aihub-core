"""The store step only ever delegates (ADR `2026_09_11_async_user_memory_storage_as_the_only_mode`).

Pinned here because the step used to branch on a config flag between an inline mem0 write and this
delegation. The inline branch is what made the blueprint announce `StoreUserMemoryEvent` and what made the
dispatcher inject `AgentMemory` into the step, so both are asserted gone: the announced event set is part of
the blueprint's contract with the API, and a step parameter is resolved by type, not by name.
"""

from unittest.mock import MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    LLMEvent,
    MemoryStorageRequestedEvent,
    Message,
    StoreUserMemoryEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.memory_writer_agent.configs.memory_writer_agent_config import MemoryWriterAgentConfig
from swiss_ai_hub.agent.agents.rag_agent import RAGAgent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.user_memory_config import UserMemoryConfig

MEMORY_MODEL = "text-generation/memory-model"


def _topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="RAGAgent",
        agent_id="hr",
        thread_id="t1",
        display_id="d1",
        run_id="r1",
        event_type="control_event",
        event_name="X",
        event_id="e1",
    )


def _config() -> RAGAgentConfig:
    return RAGAgentConfig(
        agent_id="hr",
        name=LocaleString(en="HR"),
        description=LocaleString(en="HR agent"),
        llm=LLMConfig(model_name="text-generation/main-model"),
        retrievers=[],
        user_memory=UserMemoryConfig(memory_llm=MEMORY_MODEL),
    )


@pytest.mark.asyncio
async def test_the_step_delegates_to_the_memory_writer():
    """No mem0 client is constructed, which is why this runs without any infrastructure."""
    locale_handler = MagicMock()
    locale_handler.locale = "en"

    event = await RAGAgent().store_user_memory_step(
        user_message_event=UserMessageEvent(
            user=fake_user(), messages=[ChatMessage(role=MessageRole.USER, content="hi")]
        ),
        llm_event=LLMEvent(output_messages=[Message(role="assistant", content="hello")]),
        topic=_topic(),
        agent_config=_config(),
        t=locale_handler,
    )

    assert isinstance(event, MemoryStorageRequestedEvent)
    assert (event.target_agent_class, event.target_agent_id) == (
        MemoryWriterAgentConfig.AGENT_CLASS,
        MemoryWriterAgentConfig.AGENT_ID,
    )
    assert event.start_event.origin_memory_llm == MEMORY_MODEL


def test_the_blueprint_no_longer_announces_a_completed_write():
    """`StoreUserMemoryEvent` is the writer's output now — a RAG run emits only the delegation marker."""
    output_events = RAGAgent.get_output_events()

    assert MemoryStorageRequestedEvent in output_events
    assert StoreUserMemoryEvent not in output_events

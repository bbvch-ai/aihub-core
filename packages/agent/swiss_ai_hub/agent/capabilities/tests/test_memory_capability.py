"""The memory capability's contract with the spine: every step reports on every turn, and what it reports.

An identity-less run (a scheduled agent delegating to RAG carries no user) reads and writes nobody's memories;
a profile with memory off does the same. Both must still emit their block or marker, or the spine's barriers
would hold the turn forever. The storage payload is the turn's query plus the answer — never the final LLM
input, whose context blocks and client-augmented message would feed document text into fact extraction (#1753).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import MessageRole
from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextBlockEvent,
    ConversationQueryEvent,
    LLMEvent,
    MemoryStorageRequestedEvent,
    Message,
    RetrieveUserMemoryEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig, OrgMemoryReadConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_metadata import MemoryMetadata
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.memory.memory_capability import MemoryCapability
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig

MEMORY_MODULE = "swiss_ai_hub.agent.capabilities.memory.memory_capability"
QUERY = ConversationQueryEvent(query="What is the vacation policy?", condensed=True)
ANSWER = LLMEvent(output_messages=[Message.from_string(role="assistant", content="25 days")])


def _config(*, retrieval: bool = True, storage: bool = True, org: bool = True) -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="memory-test",
        name=LocaleString(en="Memory"),
        description=LocaleString(en="Memory fixture"),
        system_prompt=LocaleString(en="You are helpful."),
        llm=LLMConfig(model_name="text-generation/dummy"),
        user_memory=UserMemoryConfig(enable_user_memory_retrieval=retrieval, enable_user_memory_storage=storage),
        org_memory=OrgMemoryReadConfig() if org else None,
    )


def _topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="LLMWrappingAgent",
        agent_id="memory-test",
        thread_id="t1",
        display_id="d1",
        run_id="r1",
        event_type="control_event",
        event_name="X",
        event_id="e1",
    )


def _memory(text: str) -> Memory:
    return Memory(
        id="m-1",
        owner_id="user-1",
        memory=text,
        score=0.9,
        created_at="2026-09-07T00:00:00Z",
        metadata=MemoryMetadata(
            user_id="user-1",
            agent_id="memory-test",
            thread_id="t1",
            display_id="d1",
            run_id="r1",
            type=MemoryType.USER_MEMORY,
        ),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config", "user"),
    [(_config(retrieval=False), fake_user()), (_config(), None)],
    ids=["retrieval-off", "no-identity"],
)
async def test_user_memory_reports_an_empty_block_without_touching_the_memory_service(config, user):
    with patch(f"{MEMORY_MODULE}.build_agent_memory") as build:
        events = await MemoryCapability.retrieve_user_memory_step(
            LLMWrappingAgent(), query=QUERY, agent_config=config, memory=config, t=LocaleHandler(), user=user
        )

    build.assert_not_called()
    assert [type(event) for event in events] == [ContextBlockEvent]
    assert events[0].source == "user_memory" and events[0].is_empty


@pytest.mark.asyncio
async def test_user_memory_contributes_a_system_block_and_the_display_event_when_it_finds_something():
    retrieved = RetrieveUserMemoryEvent(memories=[_memory("The user is based in Bern")], relations=[])
    with (
        patch(f"{MEMORY_MODULE}.build_agent_memory", return_value=MagicMock()),
        patch(f"{MEMORY_MODULE}.do_retrieve_user_memory", new=AsyncMock(return_value=retrieved)),
    ):
        events = await MemoryCapability.retrieve_user_memory_step(
            LLMWrappingAgent(),
            query=QUERY,
            agent_config=_config(),
            memory=_config(),
            t=LocaleHandler(),
            user=fake_user(),
        )

    assert [type(event) for event in events] == [RetrieveUserMemoryEvent, ContextBlockEvent]
    block = events[1]
    assert not block.is_empty
    assert all(message.role == MessageRole.SYSTEM for message in block.messages)
    assert "Bern" in (block.messages[0].content or "")


@pytest.mark.asyncio
async def test_organization_memory_reports_an_empty_block_when_the_profile_reads_none():
    run_context = MagicMock(get=AsyncMock(return_value=[]))
    with patch(f"{MEMORY_MODULE}.build_agent_memory") as build:
        events = await MemoryCapability.retrieve_organization_memory_step(
            LLMWrappingAgent(),
            query=QUERY,
            agent_config=_config(org=False),
            memory=_config(org=False),
            t=LocaleHandler(),
            run_context=run_context,
            user=fake_user(),
        )

    build.assert_not_called()
    assert [type(event) for event in events] == [ContextBlockEvent]
    assert events[0].source == "organization_memory" and events[0].is_empty


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config", "user"),
    [(_config(storage=False), fake_user()), (_config(), None)],
    ids=["storage-off", "no-identity"],
)
async def test_storage_reports_the_marker_alone_when_there_is_nothing_to_write(config, user):
    events = await MemoryCapability.store_user_memory_step(
        LLMWrappingAgent(),
        llm_event=ANSWER,
        query=QUERY,
        agent_config=config,
        memory=config,
        topic=_topic(),
        t=LocaleHandler(),
        user=user,
    )

    assert [type(event) for event in events] == [AnswerPostProcessedEvent]
    assert events[0].source == "user_memory"


@pytest.mark.asyncio
async def test_storage_delegates_the_query_and_the_answer_then_reports():
    """The request goes out ahead of the marker, so the stop step can never overtake it."""
    events = await MemoryCapability.store_user_memory_step(
        LLMWrappingAgent(),
        llm_event=ANSWER,
        query=QUERY,
        agent_config=_config(),
        memory=_config(),
        topic=_topic(),
        t=LocaleHandler(),
        user=fake_user(),
    )

    assert [type(event) for event in events] == [MemoryStorageRequestedEvent, AnswerPostProcessedEvent]
    payload = events[0].start_event.messages
    assert [message.role for message in payload] == [MessageRole.USER, MessageRole.ASSISTANT]
    assert [message.content for message in payload] == [QUERY.query, "25 days"]

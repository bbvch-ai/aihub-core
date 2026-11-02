"""The memory capability's contract: `recall` always answers, `remember` only delegates when there is something
to write.

An identity-less run (a scheduled agent delegating to RAG carries no user) reads and writes nobody's memories;
a profile with memory off does the same. Both still answer the recall so a step waiting on it never hangs. The
storage payload is the turn's query plus the answer — never the final LLM input, whose context blocks and
client-augmented message would feed document text into fact extraction (#1753).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import MessageRole
from swiss_ai_hub.core.events.agent import (
    LLMEvent,
    MemoryRecalledEvent,
    MemoryStorageRequestedEvent,
    Message,
    RetrieveOrganizationMemoryEvent,
    RetrieveUserMemoryEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig, OrgMemoryReadConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory as StoredMemory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_metadata import MemoryMetadata
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig

MEMORY_MODULE = "swiss_ai_hub.agent.capabilities.memory.memory"
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


def _memory(text: str) -> StoredMemory:
    return StoredMemory(
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


async def _recall(config: LLMWrappingAgentConfig, user, query: str = "What is the vacation policy?"):
    return await Memory.recall_step(
        LLMWrappingAgent(),
        request=Memory.recall(query),
        agent_config=config,
        memory=config,
        t=LocaleHandler(),
        user=user,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("config", "user"),
    [(_config(retrieval=False, org=False), fake_user()), (_config(org=False), None)],
    ids=["memory-off", "no-identity"],
)
async def test_recall_answers_empty_without_touching_the_memory_service(config, user):
    with patch(f"{MEMORY_MODULE}.build_agent_memory") as build:
        events = await _recall(config, user)

    build.assert_not_called()
    assert [type(event) for event in events] == [MemoryRecalledEvent]
    assert events[0].blocks == [[], []]


@pytest.mark.asyncio
async def test_a_blank_query_is_not_searched():
    with patch(f"{MEMORY_MODULE}.build_agent_memory") as build:
        events = await _recall(_config(), fake_user(), query="   ")

    build.assert_not_called()
    assert [type(event) for event in events] == [MemoryRecalledEvent]


@pytest.mark.asyncio
async def test_recall_answers_with_both_blocks_and_the_display_events():
    user_hit = RetrieveUserMemoryEvent(memories=[_memory("The user is based in Bern")], relations=[])
    org_hit = RetrieveOrganizationMemoryEvent(memories=[_memory("Offices close on Berchtoldstag")], relations=[])
    with (
        patch(f"{MEMORY_MODULE}.build_agent_memory", return_value=MagicMock()),
        patch(f"{MEMORY_MODULE}.do_retrieve_user_memory", new=AsyncMock(return_value=user_hit)),
        patch(f"{MEMORY_MODULE}.do_retrieve_organization_memory", new=AsyncMock(return_value=org_hit)),
    ):
        events = await _recall(_config(), fake_user())

    assert [type(event) for event in events] == [
        RetrieveUserMemoryEvent,
        RetrieveOrganizationMemoryEvent,
        MemoryRecalledEvent,
    ]
    recalled = events[-1]
    assert all(message.role == MessageRole.SYSTEM for block in recalled.blocks for message in block)
    assert "Bern" in (recalled.user_block[0].content or "")
    assert "Berchtoldstag" in (recalled.organization_block[0].content or "")


@pytest.mark.parametrize(
    ("config", "user"),
    [(_config(storage=False), fake_user()), (_config(), None)],
    ids=["storage-off", "no-identity"],
)
def test_remember_has_nothing_to_delegate_when_there_is_nothing_to_write(config, user):
    delegation = Memory.remember(
        query="What is the vacation policy?",
        answer=ANSWER,
        user=user,
        topic=_topic(),
        agent_config=config,
        memory=config,
        locale="en",
    )
    assert delegation is None


def test_remember_delegates_the_query_and_the_answer():
    delegation = Memory.remember(
        query="What is the vacation policy?",
        answer=ANSWER,
        user=fake_user(),
        topic=_topic(),
        agent_config=_config(),
        memory=_config(),
        locale="en",
    )

    assert isinstance(delegation, MemoryStorageRequestedEvent)
    payload = delegation.start_event.messages
    assert [message.role for message in payload] == [MessageRole.USER, MessageRole.ASSISTANT]
    assert [message.content for message in payload] == ["What is the vacation policy?", "25 days"]

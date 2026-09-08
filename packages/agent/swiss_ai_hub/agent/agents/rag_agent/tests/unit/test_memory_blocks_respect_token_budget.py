"""Memory blocks are inside the token budget, not added on top of it.

`add_memory_to_chat_history_step` extends the *already-limited* history (#1753), so without a re-limit
`extended_history` could exceed `number_of_input_tokens` — and every consumer reads it unchecked:
`context_sufficient_guard` formats it straight into a prompt, `do_respond_with_llm`'s reject paths prepend a
system message and send it, and `limit_chat_history_with_context` *reserves* system messages rather than
trimming them, so an oversized block raises there instead of being cut.

Before the reorder this was structurally impossible: memory was added to the raw history and the single
limiter ran afterwards. These tests pin that invariant back in place, including which side loses when the
result does not fit.
"""

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    LimitChatHistoryEvent,
    RetrieveUserMemoryEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import EmbeddingModelConfig, KnowledgeRetrieverConfig, LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure.mem0.types.memory import Memory
from swiss_ai_hub.core.infrastructure.mem0.types.memory_metadata import MemoryMetadata
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent

_MODEL = "text-generation/gemma-4-31B-it"


def _config(number_of_input_tokens: int) -> RAGAgentConfig:
    return RAGAgentConfig(
        agent_id="budget-test",
        name=LocaleString(en="Budget Test"),
        description=LocaleString(en="Fixture profile for the memory token-budget invariant"),
        llm=LLMConfig(model_name=_MODEL),
        number_of_input_tokens=number_of_input_tokens,
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
                vector_store=MilvusVectorStoreConfig(collection_name="bucket", index_namespaces=["ns"]),
            )
        ],
        user_memory=UserMemoryConfig(enable_user_memory_retrieval=True, enable_user_memory_storage=False),
    )


def _memories(count: int, filler: str) -> list[Memory]:
    return [
        Memory(
            id=f"m-{index}",
            owner_id="user-1",
            memory=f"{filler} {index}",
            score=0.9,
            created_at="2026-09-07T00:00:00Z",
            metadata=MemoryMetadata(
                user_id="user-1",
                agent_id="budget-test",
                thread_id="thread-1",
                display_id="display-1",
                run_id="run-1",
                type=MemoryType.USER_MEMORY,
            ),
        )
        for index in range(count)
    ]


def _turns(count: int) -> list[ChatMessage]:
    return [
        ChatMessage(
            role=MessageRole.USER if index % 2 == 0 else MessageRole.ASSISTANT,
            content=f"turn {index} " + "padding " * 40,
        )
        for index in range(count)
    ]


async def _run_step(agent_type, config: RAGAgentConfig, history: list[ChatMessage], memories: list[Memory]):
    return await agent_type().add_memory_to_chat_history_step(
        chat_history_event=LimitChatHistoryEvent(limited_history=history),
        start_event=UserMessageEvent(
            messages=history,
            user=fake_user(),
        ),
        user_memory_event=RetrieveUserMemoryEvent(memories=memories, relations=[]),
        org_memory_event=None,
        agent_config=config,
        t=LocaleHandler(),
    )


def _token_count(config: RAGAgentConfig, messages: list[ChatMessage]) -> int:
    counter = config.llm.token_counter
    return sum(len(counter(message.content or "")) for message in messages)


@pytest.mark.parametrize("agent_type", [RAGAgent, ExpertRAGAgent], ids=lambda agent: agent.__name__)
@pytest.mark.asyncio
async def test_extended_history_stays_within_the_configured_budget(agent_type):
    """A budget too small for history plus memory must yield a history that still fits it."""
    config = _config(number_of_input_tokens=600)

    event = await _run_step(agent_type, config, _turns(12), _memories(10, "The user prefers a very specific thing"))

    assert _token_count(config, event.extended_history) <= config.number_of_input_tokens


@pytest.mark.parametrize("agent_type", [RAGAgent, ExpertRAGAgent], ids=lambda agent: agent.__name__)
@pytest.mark.asyncio
async def test_memory_block_survives_when_the_budget_is_ample(agent_type):
    """The point of the step is still the memory block — a generous budget must keep it."""
    config = _config(number_of_input_tokens=128000)

    event = await _run_step(agent_type, config, _turns(4), _memories(3, "The user is based in Bern"))

    system_messages = [m for m in event.extended_history if m.role == MessageRole.SYSTEM]
    assert system_messages, "the memory block was dropped despite a 128k budget"
    assert "Bern" in "\n".join(m.content or "" for m in system_messages)


@pytest.mark.parametrize("agent_type", [RAGAgent, ExpertRAGAgent], ids=lambda agent: agent.__name__)
@pytest.mark.asyncio
async def test_the_memory_block_is_what_gives_way_not_the_latest_turn(agent_type):
    """When it cannot all fit, the optional context loses and the question the user asked survives.

    `ChatMemoryBuffer` keeps the most recent messages and the block sits at the front, so this falls out of
    the limiter rather than being enforced here — the test exists because the opposite behaviour would be a
    silent regression, not a visible one.
    """
    config = _config(number_of_input_tokens=200)
    history = _turns(10)

    event = await _run_step(agent_type, config, history, _memories(10, "A long remembered fact about the user"))

    assert event.extended_history, "limiting must never empty the history"
    assert event.extended_history[-1].content == history[-1].content

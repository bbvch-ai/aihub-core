"""A RAG answer is composed once its outcome is known, so the composed context the chat shows is exactly the prompt
the model answers from: the retrieved documents on acceptance, the rejection's reason otherwise, and for the expert
blueprint the expert's reply."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    AttachedFilesReadEvent,
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    ConversationContextualizedEvent,
    ExpertRejectEvent,
    FewShotRejectEvent,
    KnowledgeSearchedEvent,
    MemoryRecalledEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import EmbeddingModelConfig, KnowledgeRetrieverConfig, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.events.expert_answer_context_event import ExpertAnswerContextEvent
from swiss_ai_hub.agent.agents.rag_agent.events.in_order_node_combiner_event import InOrderNodeCombinerEvent
from swiss_ai_hub.agent.agents.rag_agent.rag_agent import RAGAgent
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)

RAG_MODULE = "swiss_ai_hub.agent.agents.rag_agent.rag_agent"
T = AgentLocaleHandler("en")
QUESTION = ChatMessage(role=MessageRole.USER, content="What is AI Hub?")
DOCUMENTS = InOrderNodeCombinerEvent(
    context_message=ChatMessage(role=MessageRole.USER, content="<REFERENCE_DOCUMENT>AI Hub is a platform."),
)
MEMORY = [ChatMessage(role=MessageRole.SYSTEM, content="The user works in Bern.")]


def _config() -> RAGAgentConfig:
    return RAGAgentConfig(
        agent_id="answer-prompt",
        name=LocaleString(en="Answer Prompt"),
        description=LocaleString(en="Fixture profile"),
        system_prompt=LocaleString(en="You answer from the documents."),
        llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
                vector_store=MilvusVectorStoreConfig(collection_name="bucket", index_namespaces=["ns"]),
            )
        ],
    )


async def _compose(agent, outcome, documents=None):
    return await agent.assemble_prompt_step(
        outcome=outcome,
        ctx=ConversationContextualizedEvent(history=[QUESTION], query="What is AI Hub?"),
        memories=MemoryRecalledEvent(user_block=MEMORY),
        files=AttachedFilesReadEvent(),
        knowledge=KnowledgeSearchedEvent(),
        start_event=UserMessageEvent(messages=[QUESTION], user=fake_user()),
        agent_config=_config(),
        guard_config=ContextSufficientGuardStepConfig(context_insufficient_prompt=LocaleString(en="Say you cannot.")),
        t=T,
        documents=documents,
    )


def _texts(messages: list[ChatMessage]) -> str:
    return "\n".join(message.content or "" for message in messages)


@pytest.mark.parametrize("agent", [RAGAgent(), ExpertRAGAgent()], ids=lambda agent: type(agent).__name__)
@pytest.mark.asyncio
async def test_an_accepted_context_puts_the_documents_into_the_system_head(agent):
    request = await _compose(agent, ContextSufficientAcceptEvent(reason="enough"), DOCUMENTS)

    assert request.history[0].content.startswith("You answer from the documents.")
    assert request.history[-1] == QUESTION
    assert request.blocks[0] == MEMORY
    assert request.blocks[-1][0].role == MessageRole.SYSTEM, "the documents join the system head, not the turns"
    assert "AI Hub is a platform." in request.blocks[-1][0].content


@pytest.mark.parametrize(
    ("agent", "rejection"),
    [
        (RAGAgent(), FewShotRejectEvent(reason="off topic")),
        (RAGAgent(), ContextInsufficientRejectEvent(reason="nothing found")),
        (ExpertRAGAgent(), FewShotRejectEvent(reason="off topic")),
        (ExpertRAGAgent(), ExpertRejectEvent(reason="declined")),
    ],
    ids=lambda value: type(value).__name__,
)
@pytest.mark.asyncio
async def test_a_rejection_answers_with_its_reason_and_without_documents(agent, rejection):
    request = await _compose(agent, rejection, DOCUMENTS)

    assert rejection.reason in _texts(request.history)
    assert "Say you cannot." in _texts(request.history)
    assert "AI Hub is a platform." not in _texts([message for block in request.blocks for message in block])


@pytest.mark.asyncio
async def test_the_expert_reply_is_the_context_of_an_escalated_answer():
    reply = ExpertAnswerContextEvent(context_message=ChatMessage(role=MessageRole.SYSTEM, content="The expert says X."))

    request = await _compose(ExpertRAGAgent(), reply, DOCUMENTS)

    assert request.blocks[-1][0].content == "The expert says X."
    assert "AI Hub is a platform." not in _texts([message for block in request.blocks for message in block])


@pytest.mark.parametrize("agent", [RAGAgent(), ExpertRAGAgent()], ids=lambda agent: type(agent).__name__)
@pytest.mark.asyncio
async def test_the_sufficiency_guard_weighs_the_documents_against_the_gathered_context(agent):
    """A recalled memory or an attached file may already answer the question, so the guard sees them too."""
    attached_file = [ChatMessage(role=MessageRole.SYSTEM, content="<REFERENCE_DOCUMENT>The handbook says Y.")]

    with patch(f"{RAG_MODULE}.do_context_sufficient_guard", new=AsyncMock()) as guard:
        await agent.context_sufficient_guard_step(
            agent_config=_config(),
            guard_config=ContextSufficientGuardStepConfig(),
            displayer=MagicMock(),
            t=T,
            event=DOCUMENTS,
            ctx=ConversationContextualizedEvent(history=[QUESTION], query="What is AI Hub?"),
            memories=MemoryRecalledEvent(user_block=MEMORY),
            files=AttachedFilesReadEvent(block=attached_file),
            knowledge=KnowledgeSearchedEvent(),
            run_context=MagicMock(),
        )

    seen = _texts(guard.await_args.kwargs["chat_history"])
    assert "The user works in Bern." in seen
    assert "The handbook says Y." in seen
    assert guard.await_args.kwargs["chat_history"][-1] == QUESTION

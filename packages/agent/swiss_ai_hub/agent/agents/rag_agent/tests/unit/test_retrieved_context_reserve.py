"""The room a RAG profile keeps free for retrieved knowledge and the sufficiency guard when attached files are sized."""

from unittest.mock import patch

from llama_index.core.utils import get_tokenizer
from swiss_ai_hub.core.generative_ai import (
    KnowledgeRetrieverConfig,
    LLMConfig,
    RerankingModelConfig,
    context_sufficient_guard_messages,
    estimate_prompt_tokens,
)
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString

from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)


def _config(
    retrieve_k: int = 5, reranking_top_n: int | None = None, check_context_sufficiency: bool = False
) -> RAGAgentConfig:
    retriever = KnowledgeRetrieverConfig.model_construct(retrieve_k=retrieve_k, retrieve_prev_next=None)
    reranking = (
        RerankingConfig.model_construct(
            reranking_model=RerankingModelConfig(model_name="reranker/bge", top_n=reranking_top_n)
        )
        if reranking_top_n
        else None
    )
    return RAGAgentConfig.model_construct(
        agent_id="rag",
        name=LocaleString(en="RAG"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        retrievers=[retriever],
        reranking_config=reranking,
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=check_context_sufficiency),
    )


def test_reserve_covers_every_retrieved_node():
    with patch.object(ConversationFields, "input_budget", return_value=1_000_000):
        assert (
            _config(retrieve_k=5).retrieved_context_reserve()
            == 5 * RAGAgentConfig.model_fields["retrieved_tokens_per_node"].default
        )


def test_reranking_narrows_the_reserve_to_its_top_n():
    with patch.object(ConversationFields, "input_budget", return_value=1_000_000):
        assert (
            _config(retrieve_k=20, reranking_top_n=3).retrieved_context_reserve()
            == 3 * RAGAgentConfig.model_fields["retrieved_tokens_per_node"].default
        )


def test_reserve_never_exceeds_half_the_budget():
    with patch.object(ConversationFields, "input_budget", return_value=10_000):
        assert _config(retrieve_k=100).retrieved_context_reserve() == 5_000


def test_without_the_sufficiency_guard_nothing_is_reserved_for_it():
    assert _config().context_sufficient_guard_reserve(LocaleHandler(locale="en"), "Which torque applies?") == 0


def test_the_guard_reserve_covers_its_instructions_and_the_query():
    t = LocaleHandler(locale="en")
    guard_prompt = context_sufficient_guard_messages(
        t=t,
        user_query="Which torque applies?",
        context_message=None,
        prev_queries=[],
        more_hops_available=True,
        chat_history=[],
    )

    reserve = _config(check_context_sufficiency=True).context_sufficient_guard_reserve(t, "Which torque applies?")

    assert reserve == estimate_prompt_tokens(guard_prompt, get_tokenizer())
    assert reserve > _config(check_context_sufficiency=True).context_sufficient_guard_reserve(t, None)

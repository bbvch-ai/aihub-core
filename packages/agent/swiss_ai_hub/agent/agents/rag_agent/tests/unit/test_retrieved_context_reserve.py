"""The room a RAG profile keeps free for retrieved knowledge when attached files are sized."""

from unittest.mock import patch

from swiss_ai_hub.core.generative_ai import KnowledgeRetrieverConfig, LLMConfig, RerankingModelConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.rag_agent.configs.rag_agent_config import RETRIEVED_TOKENS_PER_NODE, RAGAgentConfig
from swiss_ai_hub.agent.agents.rag_agent.configs.reranking_config import RerankingConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields


def _config(retrieve_k: int, reranking_top_n: int | None = None) -> RAGAgentConfig:
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
    )


def test_reserve_covers_every_retrieved_node():
    with patch.object(ConversationFields, "input_budget", return_value=1_000_000):
        assert _config(retrieve_k=5).retrieved_context_reserve() == 5 * RETRIEVED_TOKENS_PER_NODE


def test_reranking_narrows_the_reserve_to_its_top_n():
    with patch.object(ConversationFields, "input_budget", return_value=1_000_000):
        assert _config(retrieve_k=20, reranking_top_n=3).retrieved_context_reserve() == 3 * RETRIEVED_TOKENS_PER_NODE


def test_reserve_never_exceeds_half_the_budget():
    with patch.object(ConversationFields, "input_budget", return_value=10_000):
        assert _config(retrieve_k=100).retrieved_context_reserve() == 5_000

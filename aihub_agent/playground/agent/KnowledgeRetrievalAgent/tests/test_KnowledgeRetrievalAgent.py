import asyncio
from pathlib import Path

import pytest
from aihub_lib.agents.step_configs import KnowledgeRetrievalStepConfig
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrievalResponseEvent, RetrievalStartEvent, RetrieverEvent
from aihub_lib.persistence.rag.documents.stores.docstore import create_mongo_document_store
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from aihub_lib.testing.asyncio_utils.bdd import async_test
from aihub_lib.testing.milvus_vector_store_content import drop_collection, fill_collection
from dotenv import load_dotenv
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.KnowledgeRetrievalAgent.configs.KnowledgeRetrievalAgentConfig import (
    KnowledgeRetrievalAgentConfig,
)
from aihub_agent.agents.KnowledgeRetrievalAgent.KnowledgeRetrievalAgent import KnowledgeRetrievalAgent
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.rag.events import InOrderNodeCombinerEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("../tests/features/knowledge_retrieval_agent.feature")
load_dotenv(Path(__file__).parent / ".env")


def build_knowledge_retrieval_agent_config(
    embedding_config: EmbeddingModelConfig,
    vector_store: MilvusVectorStoreConfig,
    query_mode: VectorStoreQueryMode,
    reranking_config: RerankingConfig | None = None,
) -> KnowledgeRetrievalAgentConfig:
    """Build a KnowledgeRetrievalAgentConfig for testing."""
    return KnowledgeRetrievalAgentConfig(
        agent_id="knowledge_retrieval_agent",
        agent_class=KnowledgeRetrievalAgent.__name__,
        name=LocaleString(en="Knowledge Retrieval Agent"),
        description=LocaleString(en="Agent for retrieving knowledge from vector stores"),
        icon="robot",
        retrieval=KnowledgeRetrievalStepConfig(
            embed_model=embedding_config,
            vector_store=vector_store,
            namespaces=["ai_knowledge"],
            retrieve_k=5,
            query_mode=query_mode,
            node_types=["content"],
            retrieve_prev_next=RetrievePrevNextConfig(
                num_nodes=2,
                mode=ModeOptions.BOTH,
            ),
        ),
        reranking_config=reranking_config or RerankingConfig(),
    )


@pytest.fixture(scope="function")
def self_hosted_agent_config(event_loop):
    """Set up agent config for self-hosted testing."""
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/large")
    vector_store = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="knowledge_retrieval_agent_development",
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="knowledge_retrieval_agent_development")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield build_knowledge_retrieval_agent_config(
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
    )

    drop_collection(collection_name="knowledge_retrieval_agent_development")


@pytest.mark.usefixtures("self_hosted_agent_config")
@given("a KnowledgeRetrievalAgent and a vector store with 3 documents about AI", target_fixture="agent_runner")
def _(self_hosted_agent_config):
    """Given a KnowledgeRetrievalAgent runner with a valid self-hosted configuration."""
    return AgentTestRunner(
        agent_type=KnowledgeRetrievalAgent,
        default_agent_config=self_hosted_agent_config,
    )


@when(parsers.parse('the user asks "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=RetrievalStartEvent(question=query, locale="en"),
        )


@then(parsers.parse('the agent should retrieve "{count:d}" nodes'))
def _(agent_runner: AgentTestRunner):
    retriever_event = agent_runner.get_event_of_class(RetrieverEvent)
    assert retriever_event.nodes, "RetrieverEvent did not produce nodes"
    assert len(retriever_event.nodes) == 3, "RetrieverEvent did not produce 3 nodes"


@then("the nodes should be combined into a single message")
def _(agent_runner: AgentTestRunner):
    combiner_event = agent_runner.get_event_of_class(InOrderNodeCombinerEvent)
    assert combiner_event.context_message, "InOrderNodeCombinerEvent did not produce context message"


@then("the agent returns an event with this context message and stops")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not produce StopEvent"
    retrieval_response_event = agent_runner.get_event_of_class(RetrievalResponseEvent)
    assert retrieval_response_event.context_message, "context message is not present in RetrievalResponseEvent"


# ==================== Reranking Scenario ====================


@pytest.fixture(scope="function")
def reranking_agent_config(event_loop):
    """Set up agent config with reranking enabled."""
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/large")
    vector_store = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="knowledge_retrieval_agent_reranking",
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="knowledge_retrieval_agent_reranking")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield build_knowledge_retrieval_agent_config(
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
        reranking_config=RerankingConfig(
            enabled=True,
            reranking_model=RerankingModelConfig(model_name="reranker", top_n=2),
        ),
    )

    drop_collection(collection_name="knowledge_retrieval_agent_reranking")


@pytest.mark.usefixtures("reranking_agent_config")
@given(
    parsers.parse('a KnowledgeRetrievalAgent with reranking enabled and top_n of "{top_n:d}"'),
    target_fixture="agent_runner",
)
def _(reranking_agent_config, top_n: int):
    """Given a KnowledgeRetrievalAgent runner with reranking enabled."""
    reranking_agent_config.reranking_config.reranking_model.top_n = top_n
    return AgentTestRunner(
        agent_type=KnowledgeRetrievalAgent,
        default_agent_config=reranking_agent_config,
    )


@then(parsers.parse('a RetrieverEvent is present with more than "{node_count:d}" retrieved nodes'))
def _(agent_runner: AgentTestRunner, node_count: int):
    retriever_event = agent_runner.get_event_of_class(RetrieverEvent)
    nodes = len(retriever_event.nodes)
    assert nodes > node_count, f"Expected more than {node_count} nodes, got {nodes}"


@then("a RerankerEvent is present with reranked nodes")
def _(agent_runner: AgentTestRunner):
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)
    assert reranker_event, "RerankerEvent was not produced"
    assert reranker_event.output_nodes, "RerankerEvent did not contain reranked nodes"


@then(parsers.parse('the RerankerEvent model name should be "{model_name}"'))
def _(agent_runner: AgentTestRunner, model_name: str):
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)
    assert reranker_event, "RerankerEvent was not found"
    assert (
        reranker_event.rerank_model_name == model_name
    ), f"Expected model {model_name}, got {reranker_event.rerank_model_name}"


@then(parsers.parse('the RerankerEvent should limit results to "{top_n:d}" nodes'))
def _(agent_runner: AgentTestRunner, top_n: int):
    reranker_event = agent_runner.get_event_of_class(RerankerEvent)
    assert reranker_event, "RerankerEvent was not found"
    assert (
        len(reranker_event.output_nodes) <= top_n
    ), f"Expected at most {top_n} nodes, got {len(reranker_event.output_nodes)}"

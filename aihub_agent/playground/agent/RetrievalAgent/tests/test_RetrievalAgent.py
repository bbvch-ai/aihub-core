import asyncio
from pathlib import Path

import pytest
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig
from aihub_lib.generative_ai.retrievers import InsightRetrieverConfig, KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.persistence.insight.InsightEntity import InsightCreator, InsightEntity, InsightMessage, InsightSource
from aihub_lib.persistence.rag.documents.stores.docstore import create_mongo_document_store
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from aihub_lib.testing.asyncio_utils.bdd import async_test
from aihub_lib.testing.milvus_vector_store_content import drop_collection, fill_collection
from dotenv import load_dotenv
from llama_index.core.base.llms.types import MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.agents.RetrievalAgent.configs.RetrievalAgentConfig import RetrievalAgentConfig
from aihub_agent.agents.RetrievalAgent.events.QuestionStartEvent import QuestionStartEvent
from aihub_agent.agents.RetrievalAgent.events.RetrievalResponseEvent import RetrievalResponseEvent
from aihub_agent.agents.RetrievalAgent.RetrievalAgent import RetrievalAgent
from aihub_agent.rag.events import InOrderNodeCombinerEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


# Set up an event loop for the test session
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("../tests/features/retrieval_agent.feature")
load_dotenv(Path(__file__).parent / ".env")


def build_retrieval_agent_config(
    embedding_config,
    vector_store,
    query_mode: VectorStoreQueryMode,
) -> RetrievalAgentConfig:
    """
    Build a fully populated RetrievalAgentConfig, substituting in the embedding config
    and vector store that differ between Azure vs. Self-Hosted.

    We keep the entire parameter list intact to avoid partial Pydantic construction.
    """
    return RetrievalAgentConfig(
        agent_id="retrieval_agent",
        agent_class=RetrievalAgent.__name__,
        name=LocaleString(en="Retrieval Agent"),
        description=LocaleString(en="This is an agent that can be used to answer user questions using RAG"),
        icon="robot",
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=embedding_config,
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode=query_mode,
                node_types=["content"],
                vector_store=vector_store,
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=2,
                    mode=ModeOptions.BOTH,
                ),
            ),
        ],
    )


@pytest.fixture(scope="function")
def self_hosted_agent_config(event_loop):
    # Set the event loop for this function
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/large")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="retrieval_agent_development",
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="retrieval_agent_development")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield build_retrieval_agent_config(
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
    )

    drop_collection(collection_name="retrieval_agent_development")


@pytest.mark.usefixtures("self_hosted_agent_config")
@given("a RetrievalAgent and a vector store with 3 documents about AI", target_fixture="agent_runner")
def _(self_hosted_agent_config):
    """
    Given a RAGAgent runner with a valid self-hosted configuration.
    """
    return AgentTestRunner(
        agent_type=RetrievalAgent,
        default_agent_config=self_hosted_agent_config,
    )


@when(parsers.parse('the user asks "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=120) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=QuestionStartEvent(question=query, locale="en"),
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


def build_retrieval_agent_config_with_reranking(
    embedding_config: EmbeddingModelConfig,
    vector_store: MilvusVectorStoreConfig,
    query_mode: VectorStoreQueryMode,
    top_n: int,
) -> RetrievalAgentConfig:
    """Build a RetrievalAgentConfig with reranking enabled."""
    return RetrievalAgentConfig(
        agent_id="retrieval_agent_reranking",
        agent_class=RetrievalAgent.__name__,
        name=LocaleString(en="Retrieval Agent with Reranking"),
        description=LocaleString(en="Retrieval agent with reranking enabled"),
        icon="robot",
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=embedding_config,
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode=query_mode,
                node_types=["content"],
                vector_store=vector_store,
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=2,
                    mode=ModeOptions.BOTH,
                ),
            ),
        ],
        reranking_config=RerankingConfig(
            enabled=True,
            reranking_model=RerankingModelConfig(model_name="reranker", top_n=top_n),
        ),
    )


@pytest.fixture(scope="function")
def reranking_agent_config(event_loop):
    """Set up agent config with reranking enabled."""
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/large")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="retrieval_agent_reranking",
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="retrieval_agent_reranking")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield build_retrieval_agent_config_with_reranking(
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
        top_n=2,
    )

    drop_collection(collection_name="retrieval_agent_reranking")


@pytest.mark.usefixtures("reranking_agent_config")
@given(
    parsers.parse('a RetrievalAgent with reranking enabled and top_n of "{top_n:d}"'),
    target_fixture="agent_runner",
)
def _(reranking_agent_config, top_n: int):
    """Given a RetrievalAgent runner with reranking enabled."""
    # Update top_n if different from fixture default
    reranking_agent_config.reranking_config.reranking_model.top_n = top_n
    return AgentTestRunner(
        agent_type=RetrievalAgent,
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


# ==================== Insights Scenario ====================

TEST_INSIGHT_NAMESPACE = "ai_knowledge"
TEST_INSIGHT_AGENT_CLASS = "RetrievalAgent"
TEST_INSIGHT_AGENT_ID = "retrieval_agent"


def create_test_insights(namespace: str, agent_class: str, agent_id: str) -> list[InsightEntity]:
    """Pre-seed MongoDB with test insights for retrieval tests."""
    insights = []
    insight1 = InsightEntity.create_insight(
        question="What is machine learning?",
        expert_answer="Machine learning is a subset of AI that enables systems to learn from data.",
        conversation=[
            InsightMessage(role=MessageRole.USER, content="What is machine learning?"),
            InsightMessage(
                role=MessageRole.ASSISTANT,
                content="Machine learning is a subset of AI that enables systems to learn from data.",
            ),
        ],
        namespace=namespace,
        source=InsightSource(thread_id="test-thread-1", expert_user_id="expert-1", expert_name="Dr. AI Expert"),
        creator=InsightCreator(agent_class=agent_class, agent_id=agent_id, user_id="test-user", user_name="Test User"),
    )
    insights.append(insight1)
    return insights


def delete_test_insights(namespace: str):
    """Cleanup test insights after tests."""
    InsightEntity.objects(namespace=namespace).delete()


@pytest.fixture(scope="session")
def mongo_connection(event_loop):
    """Set up MongoEngine connection for InsightEntity tests."""
    asyncio.set_event_loop(event_loop)
    config = AIHubSettings()
    connect(
        db=config.MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture(scope="function")
def test_insights(event_loop, mongo_connection):
    """Setup/teardown test insights for insight retrieval tests."""
    asyncio.set_event_loop(event_loop)
    insights = create_test_insights(
        namespace=TEST_INSIGHT_NAMESPACE,
        agent_class=TEST_INSIGHT_AGENT_CLASS,
        agent_id=TEST_INSIGHT_AGENT_ID,
    )
    yield insights
    # Cleanup insights - wrapped in try/except in case mongo disconnects first
    try:
        delete_test_insights(namespace=TEST_INSIGHT_NAMESPACE)
    except Exception:
        pass  # Connection may already be closed during teardown


def build_retrieval_agent_config_with_insights(
    embedding_config: EmbeddingModelConfig,
    vector_store: MilvusVectorStoreConfig,
    query_mode: VectorStoreQueryMode,
    insight_namespace: str,
    insight_agent_class: str,
    insight_agent_id: str,
) -> RetrievalAgentConfig:
    """Build RetrievalAgentConfig with both knowledge AND insight retrievers."""
    return RetrievalAgentConfig(
        agent_id="retrieval_agent_insights",
        agent_class=RetrievalAgent.__name__,
        name=LocaleString(en="Retrieval Agent with Insights"),
        description=LocaleString(en="Retrieval agent with expert insights"),
        icon="robot",
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=embedding_config,
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode=query_mode,
                node_types=["content"],
                vector_store=vector_store,
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=2,
                    mode=ModeOptions.BOTH,
                ),
            ),
            InsightRetrieverConfig(
                namespace=insight_namespace,
                agent_class=insight_agent_class,
                agent_id=insight_agent_id,
            ),
        ],
    )


@pytest.fixture(scope="function")
def insight_agent_config(event_loop, test_insights):
    """Set up agent config with insight retriever enabled."""
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/large")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="retrieval_agent_insights",
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="retrieval_agent_insights")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield build_retrieval_agent_config_with_insights(
        embedding_config=embedding_config,
        vector_store=vector_store,
        query_mode=VectorStoreQueryMode.HYBRID,
        insight_namespace=TEST_INSIGHT_NAMESPACE,
        insight_agent_class=TEST_INSIGHT_AGENT_CLASS,
        insight_agent_id=TEST_INSIGHT_AGENT_ID,
    )

    drop_collection(collection_name="retrieval_agent_insights")


@pytest.mark.usefixtures("insight_agent_config")
@given("a RetrievalAgent with insight retriever enabled", target_fixture="agent_runner")
def _(insight_agent_config):
    """Given a RetrievalAgent runner with insight retriever enabled."""
    return AgentTestRunner(
        agent_type=RetrievalAgent,
        default_agent_config=insight_agent_config,
    )


@given("test insights are pre-seeded in the database")
def _(test_insights):
    """Ensure test insights are pre-seeded in the database (handled by fixture)."""
    assert len(test_insights) > 0, "Test insights were not pre-seeded"


@then("a RetrieverEvent is present with retrieved nodes")
def _(agent_runner: AgentTestRunner):
    retriever_event = agent_runner.get_event_of_class(RetrieverEvent)
    assert retriever_event.nodes, "RetrieverEvent did not produce nodes"

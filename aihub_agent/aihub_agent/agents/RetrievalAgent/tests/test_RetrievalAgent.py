import asyncio
from pathlib import Path

import pytest
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.persistence.rag.documents.stores.docstore import create_mongo_document_store
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from aihub_lib.testing.asyncio_utils.bdd import async_test
from aihub_lib.testing.milvus_vector_store_content import drop_collection, fill_collection
from dotenv import load_dotenv
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RetrievalAgent.configs.RetrievalAgentConfig import RetrievalAgentConfig
from aihub_agent.agents.RetrievalAgent.events.QuestionStartEvent import QuestionStartEvent
from aihub_agent.agents.RetrievalAgent.events.RetrievalResponseEvent import RetrievalResponseEvent
from aihub_agent.agents.RetrievalAgent.RetrievalAgent import RetrievalAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


# Set up an event loop for the test session
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("./features/retrieval_agent.feature")
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
        retriever=KnowledgeRetrieverConfig(
            embed_model=embedding_config,
            retrieve_k=5,
            query_mode=query_mode,
            node_types=["content"],
            vector_store=vector_store,
            retrieve_prev_next=RetrievePrevNextConfig(
                num_nodes=2,
                mode=ModeOptions.BOTH,
            ),
        ),
    )


@pytest.fixture(scope="function")
def self_hosted_agent_config(event_loop):
    # Set the event loop for this function
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        collection_name="retrieval_agent_development",
        dimensions=1024,
        index_namespaces=["ai_knowledge"],
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
        agent_config=self_hosted_agent_config,
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

# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig
from aihub_lib.generative_ai.retrievers import KnowledgeRetrieverConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.nats.events import LLMEvent, UserMessageEvent
from aihub_lib.nats.events.agent_in_the_loop import AgentInTheLoopRequestEvent, AgentInTheLoopResponseEvent
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig
from aihub_lib.nats.events.guard import ExpertRejectEvent
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoopConfirmation
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopConfirmationRequestEvent,
)
from aihub_lib.persistence.rag.documents.stores.docstore import create_mongo_document_store
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from aihub_lib.testing.asyncio_utils.bdd import async_test
from aihub_lib.testing.milvus_vector_store_content import drop_collection, fill_collection
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from aihub_agent.agents.RagAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()

scenarios("./features/rag_agent_expert_escalation.feature")
load_dotenv(Path(__file__).parent / ".env")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_collection(event_loop):
    """Set up and tear down the test collection for all tests."""
    asyncio.set_event_loop(event_loop)

    embedding_config = EmbeddingModelConfig(model_name="embedding/large")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="development",
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="development")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store,
    )

    yield

    drop_collection()


@pytest.fixture(scope="session")
def mongo_connection(event_loop):
    """Set up MongoEngine connection for tests."""
    asyncio.set_event_loop(event_loop)
    config = AIHubSettings()
    connect(
        db=config.MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    yield
    disconnect()


@pytest.fixture(scope="session")
def expert_escalation_agent_config(test_collection):
    """Return a RAGAgentConfig with expert escalation enabled."""
    llm_config = LLMConfig(model_name="text-generation/mini")
    reranking_config = RerankingModelConfig(model_name="reranker")
    embedding_config = EmbeddingModelConfig(model_name="embedding/large")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="development",
        dimensions=1024,
    )

    return RAGAgentConfig(
        agent_id="rag_agent",
        agent_class=RAGAgent.__name__,
        name=LocaleString(en="RAG Agent with Expert Escalation"),
        description=LocaleString(en="RAG agent with expert escalation for insufficient context"),
        llm=llm_config,
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=embedding_config,
                index_namespaces=["ai_knowledge"],
                retrieve_k=5,
                query_mode=VectorStoreQueryMode.HYBRID,
                node_types=["content"],
                vector_store=vector_store,
                retrieve_prev_next=RetrievePrevNextConfig(
                    num_nodes=2,
                    mode=ModeOptions.BOTH,
                ),
            ),
        ],
        number_of_input_tokens=8192,
        check_context_sufficiency=True,
        max_hops=1,
        expert_escalation=ExpertEscalationConfig(
            expert_asking_agent_class="ExpertAskingAgent",
            expert_asking_agent_id="test_expert_agent",
        ),
        reranking_config=RerankingConfig(enabled=False, reranking_model=reranking_config),
    )


@pytest.fixture(scope="session")
def expert_asking_agent_config(mongo_connection):
    """Return an ExpertAskingAgentConfig for tests."""
    return ExpertAskingAgentConfig(
        agent_id="test_expert_agent",
        agent_class=ExpertAskingAgent.__name__,
        name=LocaleString(en="Test Expert Asking Agent"),
        description=LocaleString(en="Mock expert asking agent for tests"),
        llm=LLMConfig(model_name="text-generation/mini"),
        loop_max=3,
        channel_config=TeamsConfig(
            channel_id="19:test-channel-id@thread.tacv2",
            tenant_id="00000000-0000-0000-0000-000000000000",
            bot_id="00000000-0000-0000-0000-000000000001",
        ),
        insight_namespace="ai_knowledge",
    )


@pytest.mark.usefixtures("expert_escalation_agent_config")
@given("a RAGAgent runner with expert escalation enabled", target_fixture="rag_agent_runner")
def _(expert_escalation_agent_config):
    """Given a RAGAgent runner with expert escalation enabled."""
    return AgentTestRunner(
        agent_type=RAGAgent,
        default_agent_config=expert_escalation_agent_config,
    )


@when(parsers.parse('a query is sent and user declines expert escalation with query "{query}"'))
@async_test
async def _(rag_agent_runner: AgentTestRunner, query: str):
    """Send a query that triggers expert escalation and user declines."""
    async with rag_agent_runner.test_run(delay_before_stop=120) as topic:
        await rag_agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )
        # Wait for HITL confirmation request
        hitl_request_event = await rag_agent_runner.wait_for_event(
            HumanInTheLoopConfirmationRequestEvent,
            timeout=120,
        )
        # User declines expert escalation
        await rag_agent_runner.send_event_from_topic(
            start_event=HumanInTheLoopConfirmation.response(response=False, request_event=hitl_request_event),
            topic=hitl_request_event.topic,
        )


@when(parsers.parse('a query is sent and user accepts expert escalation with query "{query}"'))
@async_test
async def _(rag_agent_runner: AgentTestRunner, query: str):
    """Send a query that triggers expert escalation and user accepts.

    This test mocks the expert agent's response by sending an AnswerStopEvent
    to the expert agent's topic, which the RAG agent's internal subscription picks up.
    """
    async with rag_agent_runner.test_run(delay_before_stop=120) as topic:
        await rag_agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )
        # Wait for HITL confirmation request
        hitl_request_event = await rag_agent_runner.wait_for_event(
            HumanInTheLoopConfirmationRequestEvent,
            timeout=120,
        )
        # User accepts expert escalation
        await rag_agent_runner.send_event_from_topic(
            start_event=HumanInTheLoopConfirmation.response(response=True, request_event=hitl_request_event),
            topic=topic,
        )
        # Wait for AgentInTheLoop request to expert
        await rag_agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=120)

        # Mock expert response by sending AnswerStopEvent to the expert agent's topic
        # The RAG agent's internal subscription will pick this up and convert it to AgentInTheLoopResponseEvent
        mock_expert_answer = AnswerStopEvent(
            expert_answer="Quantum entanglement in advanced medicine refers to experimental applications...",
            expert_conversation=[
                ChatMessage(role=MessageRole.ASSISTANT, content="What is quantum entanglement in medicine?"),
                ChatMessage(role=MessageRole.USER, content="It refers to experimental applications..."),
            ],
        )
        await rag_agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_expert_answer),
            topic=topic,
        )


@then("a HumanInTheLoopConfirmationRequestEvent is present")
def _(rag_agent_runner: AgentTestRunner):
    """Check that a HITL confirmation request was emitted."""
    assert rag_agent_runner.has_event_of_class(
        HumanInTheLoopConfirmationRequestEvent
    ), "HumanInTheLoopConfirmationRequestEvent was not emitted"


@then("an ExpertRejectEvent is present")
def _(rag_agent_runner: AgentTestRunner):
    """Check that an ExpertRejectEvent was emitted."""
    assert rag_agent_runner.has_event_of_class(ExpertRejectEvent), "ExpertRejectEvent was not emitted"


@then("a UserRequestsExpertEvent is present")
def _(rag_agent_runner: AgentTestRunner):
    """Check that a UserRequestsExpertEvent was emitted."""
    assert rag_agent_runner.has_event_of_class(UserRequestsExpertEvent), "UserRequestsExpertEvent was not emitted"


@then("an AgentInTheLoopRequestEvent is present")
def _(rag_agent_runner: AgentTestRunner):
    """Check that an AgentInTheLoopRequestEvent was emitted."""
    assert rag_agent_runner.has_event_of_class(AgentInTheLoopRequestEvent), "AgentInTheLoopRequestEvent was not emitted"


@then("an LLMEvent is present with a generated response")
def _(rag_agent_runner: AgentTestRunner):
    llm_event = rag_agent_runner.get_event_of_class(LLMEvent)
    response_content = llm_event.output_messages[0].content
    assert response_content, "No generated response was returned"


@then("a StopEvent is present")
def _(rag_agent_runner: AgentTestRunner):
    assert rag_agent_runner.has_stop_event, "Agent did not produce StopEvent"

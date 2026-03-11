# ruff: noqa: E402
from swiss_ai_hub.core.generative_ai.retrievers.KnowledgeRetrieverConfig import KnowledgeRetrieverConfig

from swiss_ai_hub.core.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenario, scenarios, then, when
from swiss_ai_hub.core.agents.AgentRef import AgentRef
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.events.agent.aitl.request.AgentInTheLoopRequestEvent import (
    AgentInTheLoopRequestEvent,
)
from swiss_ai_hub.core.events.agent.aitl.response.AgentInTheLoopResponseEvent import (
    AgentInTheLoopResponseEvent,
)
from swiss_ai_hub.core.events.agent.guard.ExpertRejectEvent import ExpertRejectEvent
from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopConfirmation import HumanInTheLoopConfirmation
from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopConfirmationRequestEvent import (
    HumanInTheLoopConfirmationRequestEvent,
)
from swiss_ai_hub.core.events.agent.semantic.llm.LLMEvent import LLMEvent
from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from swiss_ai_hub.core.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions
from swiss_ai_hub.core.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.RerankingModelConfig import RerankingModelConfig
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.infrastructure.mongo.MongoSettings import MongoSettings
from swiss_ai_hub.core.persistence.rag.documents.stores.docstore import create_mongo_document_store
from swiss_ai_hub.core.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test
from swiss_ai_hub.core.testing.milvus_vector_store_content import drop_collection, fill_collection

from swiss_ai_hub.agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from swiss_ai_hub.agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.ExpertRagAgent.ExpertRAGAgent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.RagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from swiss_ai_hub.agent.agents.RagAgent.configs.RerankingConfig import RerankingConfig
from swiss_ai_hub.agent.agents.RagAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()

scenarios("./features/expert_rag_agent.feature")


@scenario("features/expert_rag_agent.feature", "Test ExpertRAGAgent handles user declining expert escalation")
def test_test_expertragagent_handles_user_declining_expert_escalation():
    """Test ExpertRAGAgent with user declining expert escalation."""
    pass


@scenario("features/expert_rag_agent.feature", "Test ExpertRAGAgent expert escalation user accepts")
def test_test_expertragagent_expert_escalation_user_accepts():
    """Test ExpertRAGAgent with user accepting expert escalation."""
    pass


load_dotenv(Path(__file__).parent / ".env")

TIMEOUT = 240


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

    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
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
def expert_rag_agent_config(test_collection):
    """Return an ExpertRAGAgentConfig with expert escalation enabled."""
    llm_config = LLMConfig(model_name="text-generation/gpt-oss-120b")
    reranking_config = RerankingModelConfig(model_name="reranker/bge")
    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        uri="http://localhost",
        collection_name="development",
        dimensions=1024,
    )

    return ExpertRAGAgentConfig(
        agent_id="expert_rag_agent",
        agent_class=ExpertRAGAgent.__name__,
        name=LocaleString(en="Expert RAG Agent"),
        description=LocaleString(en="Expert RAG agent with expert escalation for insufficient context"),
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
            agent=AgentRef(
                agent_class="ExpertAskingAgent",
                agent_id="test_expert_agent",
            ),
        ),
        reranking_config=RerankingConfig(enabled=False, reranking_model=reranking_config),
    )


@pytest.mark.usefixtures("expert_rag_agent_config")
@given("an ExpertRAGAgent runner with expert escalation enabled", target_fixture="expert_rag_agent_runner")
def _(expert_rag_agent_config):
    """Given an ExpertRAGAgent runner with expert escalation enabled."""
    return AgentTestRunner(
        agent_type=ExpertRAGAgent,
        agent_config=expert_rag_agent_config,
    )


@when(parsers.parse('a query is sent and user declines expert escalation with query "{query}"'))
@async_test
async def _(expert_rag_agent_runner: AgentTestRunner, query: str):
    """Send a query that triggers expert escalation and user declines."""
    async with expert_rag_agent_runner.test_run(delay_before_stop=TIMEOUT) as topic:
        await expert_rag_agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )
        # Wait for HITL confirmation request
        hitl_request_event = await expert_rag_agent_runner.wait_for_event(
            HumanInTheLoopConfirmationRequestEvent,
            timeout=TIMEOUT,
        )
        # User declines expert escalation
        await expert_rag_agent_runner.send_event_from_topic(
            start_event=HumanInTheLoopConfirmation.response(response=False, request_event=hitl_request_event),
            topic=topic,
        )


@when(parsers.parse('a query is sent and user accepts expert escalation with query "{query}"'))
@async_test
async def _(expert_rag_agent_runner: AgentTestRunner, query: str):
    """Send a query that triggers expert escalation and user accepts.

    This test mocks the expert agent's response by sending an AnswerStopEvent
    to the expert agent's topic, which the ExpertRAGAgent's internal subscription picks up.
    """
    async with expert_rag_agent_runner.test_run(delay_before_stop=TIMEOUT) as topic:
        # Ensure the ExpertAskingAgent stream exists for agent-in-the-loop delegation
        await expert_rag_agent_runner.ensure_dependent_agent_stream("ExpertAskingAgent")

        await expert_rag_agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )
        # Wait for HITL confirmation request
        hitl_request_event = await expert_rag_agent_runner.wait_for_event(
            HumanInTheLoopConfirmationRequestEvent,
            timeout=TIMEOUT,
        )
        # User accepts expert escalation
        # Small delay to ensure agent is ready to receive response (CI timing)
        await asyncio.sleep(10)
        await expert_rag_agent_runner.send_event_from_topic(
            start_event=HumanInTheLoopConfirmation.response(response=True, request_event=hitl_request_event),
            topic=topic,
        )
        # Wait for AgentInTheLoop request to expert
        await expert_rag_agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)

        # Mock expert response by sending AnswerStopEvent to the expert agent's topic
        # The ExpertRAGAgent's internal subscription will pick this up and convert it to AgentInTheLoopResponseEvent
        mock_expert_answer = AnswerStopEvent(
            expert_answer="Quantum entanglement in advanced medicine refers to experimental applications...",
            expert_conversation=[
                ChatMessage(role=MessageRole.ASSISTANT, content="What is quantum entanglement in medicine?"),
                ChatMessage(role=MessageRole.USER, content="It refers to experimental applications..."),
            ],
        )
        await expert_rag_agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_expert_answer),
            topic=topic,
        )


@then("a HumanInTheLoopConfirmationRequestEvent is present")
def _(expert_rag_agent_runner: AgentTestRunner):
    """Check that a HITL confirmation request was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(HumanInTheLoopConfirmationRequestEvent), (
        "HumanInTheLoopConfirmationRequestEvent was not emitted"
    )


@then("an ExpertRejectEvent is present")
def _(expert_rag_agent_runner: AgentTestRunner):
    """Check that an ExpertRejectEvent was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(ExpertRejectEvent), "ExpertRejectEvent was not emitted"


@then("a UserRequestsExpertEvent is present")
def _(expert_rag_agent_runner: AgentTestRunner):
    """Check that a UserRequestsExpertEvent was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(UserRequestsExpertEvent), (
        "UserRequestsExpertEvent was not emitted"
    )


@then("an AgentInTheLoopRequestEvent is present")
def _(expert_rag_agent_runner: AgentTestRunner):
    """Check that an AgentInTheLoopRequestEvent was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(AgentInTheLoopRequestEvent), (
        "AgentInTheLoopRequestEvent was not emitted"
    )


@then("an LLMEvent is present with a generated response")
def _(expert_rag_agent_runner: AgentTestRunner):
    llm_event = expert_rag_agent_runner.get_event_of_class(LLMEvent)
    response_content = llm_event.output_messages[0].content
    assert response_content, "No generated response was returned"


@then("a StopEvent is present")
def _(expert_rag_agent_runner: AgentTestRunner):
    assert expert_rag_agent_runner.has_stop_event, "Agent did not produce StopEvent"

# ruff: noqa: E402
from swiss_ai_hub.core.generative_ai import KnowledgeRetrieverConfig

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path

import pytest
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenario, scenarios, then, when
from swiss_ai_hub.core.agents import AgentRef
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoopRequestEvent,
    AgentInTheLoopResponseEvent,
    ExpertRejectEvent,
    HumanInTheLoopConfirmation,
    HumanInTheLoopConfirmationRequestEvent,
    LLMEvent,
    RAGFailureReason,
    RAGFailureStopEvent,
    RAGSuccessStopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    LLMConfig,
    ModeOptions,
    RetrievePrevNextConfig,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings, enable_logging
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig, create_mongo_document_store
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.testing.milvus_vector_store_content import drop_collection, fill_collection

from swiss_ai_hub.agent.agents.expert_asking_agent.events.answer_stop_event import AnswerStopEvent
from swiss_ai_hub.agent.agents.expert_rag_agent.configs.expert_rag_agent_config import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.expert_rag_agent.expert_rag_agent import ExpertRAGAgent
from swiss_ai_hub.agent.agents.rag_agent.configs.expert_escalation_config import ExpertEscalationConfig
from swiss_ai_hub.agent.agents.rag_agent.events.user_requests_expert_event import UserRequestsExpertEvent
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.agent.steps.guards.context_sufficient_guard_step.context_sufficient_guard_step_config import (
    ContextSufficientGuardStepConfig,
)

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
        collection_name="development",
        index_namespaces=["ai_knowledge"],
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
    llm_config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")
    vector_store: MilvusVectorStoreConfig = MilvusVectorStoreConfig(
        collection_name="development",
        index_namespaces=["ai_knowledge"],
        dimensions=1024,
    )

    return ExpertRAGAgentConfig(
        agent_id="expert_rag_agent",
        name=LocaleString(en="Expert RAG Agent"),
        description=LocaleString(en="Expert RAG agent with expert escalation for insufficient context"),
        llm=llm_config,
        retrievers=[
            KnowledgeRetrieverConfig(
                embed_model=embedding_config,
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
        context_sufficient_guard=ContextSufficientGuardStepConfig(check_context_sufficiency=True, max_hops=1),
        expert_escalation=ExpertEscalationConfig(
            agent=AgentRef(
                agent_class="ExpertAskingAgent",
                agent_id="test_expert_agent",
            ),
        ),
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
                user=fake_user(),
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
                user=fake_user(),
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
        aitl_request = await expert_rag_agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)

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
            start_event=AgentInTheLoopResponseEvent(
                stop_event=mock_expert_answer, request_event_id=aitl_request.event_id
            ),
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
    assert expert_rag_agent_runner.has_event_of_class(
        RAGSuccessStopEvent
    ) or expert_rag_agent_runner.has_event_of_class(RAGFailureStopEvent), (
        "ExpertRAGAgent should emit a RAGSuccessStopEvent or RAGFailureStopEvent so parents can branch on the outcome"
    )


@then("a RAGFailureStopEvent with reason context_insufficient is present")
def _(expert_rag_agent_runner: AgentTestRunner):
    event = expert_rag_agent_runner.get_event_of_class(RAGFailureStopEvent)
    assert event.reason == RAGFailureReason.CONTEXT_INSUFFICIENT, (
        f"Expected reason=context_insufficient, got {event.reason}"
    )


@then("a RAGSuccessStopEvent is present")
def _(expert_rag_agent_runner: AgentTestRunner):
    assert expert_rag_agent_runner.has_event_of_class(RAGSuccessStopEvent), (
        "Expert-provided context should yield a RAGSuccessStopEvent"
    )

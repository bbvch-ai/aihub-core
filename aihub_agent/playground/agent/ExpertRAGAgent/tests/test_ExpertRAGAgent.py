# ruff: noqa: E402
"""Tests for ExpertRAGAgent with mandatory expert escalation workflow."""
from aihub_agent.agents import KnowledgeRetrievalAgent, InsightRetrievalAgent
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
from pathlib import Path

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import LLMEvent, UserMessageEvent
from aihub_lib.nats.events.agent_in_the_loop import AgentInTheLoopRequestEvent, AgentInTheLoopResponseEvent
from aihub_lib.nats.events.guard import ExpertRejectEvent
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoopConfirmation
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopConfirmationRequestEvent,
)
from aihub_lib.nats.events.semantic.retriever import RetrievalResponseEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from dotenv import load_dotenv
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertRagAgent.configs.ExpertEscalationConfig import ExpertEscalationConfig
from aihub_agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from aihub_agent.agents.ExpertRagAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
from aihub_agent.agents.ExpertRagAgent.ExpertRAGAgent import ExpertRAGAgent
from aihub_agent.agents.RagAgent.configs.RetrievalAgentReference import RetrievalAgentReference
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()

pytestmark = pytest.mark.flaky

scenarios("./features/expert_rag_agent.feature")
load_dotenv(Path(__file__).parent / ".env")

TIMEOUT = 240


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def expert_rag_agent_config():
    """Return an ExpertRAGAgentConfig with expert escalation (required).

    Note: Retrieval is handled by specialized retrieval agents via AgentInTheLoop.
    ExpertRAGAgent requires at least one retrieval agent (unified list).
    Tests mock the retrieval agent responses.
    """
    llm_config = LLMConfig(model_name="text-generation/mini")

    return ExpertRAGAgentConfig(
        agent_id="expert_rag_agent",
        agent_class=ExpertRAGAgent.__name__,
        name=LocaleString(en="Expert RAG Agent"),
        description=LocaleString(en="RAG agent with mandatory expert escalation"),
        llm=llm_config,
        # Required: at least one retrieval agent (one knowledge + one insight)
        retrieval_agents=[
            RetrievalAgentReference(agent_class=KnowledgeRetrievalAgent.__name__, agent_id="test_knowledge_agent"),
            RetrievalAgentReference(agent_class=InsightRetrievalAgent.__name__, agent_id="test_insight_agent"),
        ],
        # Required: where to write new insights
        write_insight_namespace="test_namespace",
        number_of_input_tokens=8192,
        check_context_sufficiency=True,
        max_hops=1,
        expert_escalation=ExpertEscalationConfig(
            expert_asking_agent_class="ExpertAskingAgent",
            expert_asking_agent_id="test_expert_agent",
        ),
    )


# ==================== Given Steps ====================


@pytest.mark.usefixtures("expert_rag_agent_config")
@given("an ExpertRAGAgent runner", target_fixture="expert_rag_agent_runner")
def create_expert_rag_agent_runner(expert_rag_agent_config):
    """Given an ExpertRAGAgent runner with mandatory expert escalation."""
    return AgentTestRunner(
        agent_type=ExpertRAGAgent,
        default_agent_config=expert_rag_agent_config,
    )


# ==================== When Steps ====================


@when(parsers.parse('a query is sent and user declines expert escalation with query "{query}"'))
@async_test
async def send_query_user_declines(expert_rag_agent_runner: AgentTestRunner, query: str):
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
        # Wait for first AgentInTheLoop request (both are emitted together)
        await expert_rag_agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)

        # Mock KnowledgeRetrievalAgent response with minimal context
        mock_knowledge_response = RetrievalResponseEvent(
            context_message=ChatMessage(
                role=MessageRole.SYSTEM,
                content="Retrieved context: No relevant information found.",
            ),
            nodes=[],  # Empty nodes to trigger context insufficiency
            agent_id="test_knowledge_agent",
            retrieval_type="knowledge",
        )
        await expert_rag_agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_knowledge_response),
            topic=topic,
        )

        # Mock InsightRetrievalAgent response with minimal context
        mock_insight_response = RetrievalResponseEvent(
            context_message=ChatMessage(
                role=MessageRole.SYSTEM,
                content="Retrieved context: No relevant insights found.",
            ),
            nodes=[],  # Empty nodes to trigger context insufficiency
            agent_id="test_insight_agent",
            retrieval_type="insight",
        )
        await expert_rag_agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_insight_response),
            topic=topic,
        )

        # Wait for HITL confirmation request (after context insufficient guard)
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
async def send_query_user_accepts(expert_rag_agent_runner: AgentTestRunner, query: str):
    """Send a query that triggers expert escalation and user accepts.

    This test mocks the KnowledgeRetrievalAgent, InsightRetrievalAgent, and ExpertAskingAgent responses.
    """
    async with expert_rag_agent_runner.test_run(delay_before_stop=TIMEOUT) as topic:
        await expert_rag_agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                locale="en",
            ),
        )
        # Wait for first AgentInTheLoop request (both retrieval requests are emitted together)
        await expert_rag_agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)

        # Mock KnowledgeRetrievalAgent response with minimal context
        mock_knowledge_response = RetrievalResponseEvent(
            context_message=ChatMessage(
                role=MessageRole.SYSTEM,
                content="Retrieved context: No relevant information found.",
            ),
            nodes=[],  # Empty nodes to trigger context insufficiency
            agent_id="test_knowledge_agent",
            retrieval_type="knowledge",
        )
        await expert_rag_agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_knowledge_response),
            topic=topic,
        )

        # Mock InsightRetrievalAgent response with minimal context
        mock_insight_response = RetrievalResponseEvent(
            context_message=ChatMessage(
                role=MessageRole.SYSTEM,
                content="Retrieved context: No relevant insights found.",
            ),
            nodes=[],  # Empty nodes to trigger context insufficiency
            agent_id="test_insight_agent",
            retrieval_type="insight",
        )
        await expert_rag_agent_runner.send_event_from_topic(
            start_event=AgentInTheLoopResponseEvent(stop_event=mock_insight_response),
            topic=topic,
        )

        # Wait for HITL confirmation request (after context insufficient guard)
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
        # Wait for AgentInTheLoop request to ExpertAskingAgent
        await expert_rag_agent_runner.wait_for_event(AgentInTheLoopRequestEvent, timeout=TIMEOUT)

        # Mock expert response by sending AnswerStopEvent
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


# ==================== Then Steps ====================


@then("a HumanInTheLoopConfirmationRequestEvent is present")
def check_hitl_confirmation_request(expert_rag_agent_runner: AgentTestRunner):
    """Check that a HITL confirmation request was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(
        HumanInTheLoopConfirmationRequestEvent
    ), "HumanInTheLoopConfirmationRequestEvent was not emitted"


@then("an ExpertRejectEvent is present")
def check_expert_reject_event(expert_rag_agent_runner: AgentTestRunner):
    """Check that an ExpertRejectEvent was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(ExpertRejectEvent), "ExpertRejectEvent was not emitted"


@then("a UserRequestsExpertEvent is present")
def check_user_requests_expert_event(expert_rag_agent_runner: AgentTestRunner):
    """Check that a UserRequestsExpertEvent was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(
        UserRequestsExpertEvent
    ), "UserRequestsExpertEvent was not emitted"


@then("an AgentInTheLoopRequestEvent is present")
def check_agent_in_the_loop_request(expert_rag_agent_runner: AgentTestRunner):
    """Check that an AgentInTheLoopRequestEvent was emitted."""
    assert expert_rag_agent_runner.has_event_of_class(
        AgentInTheLoopRequestEvent
    ), "AgentInTheLoopRequestEvent was not emitted"


@then("an LLMEvent is present with a generated response")
def check_llm_event_with_response(expert_rag_agent_runner: AgentTestRunner):
    """Check that an LLMEvent was emitted with a non-empty response."""
    llm_event = expert_rag_agent_runner.get_event_of_class(LLMEvent)
    response_content = llm_event.output_messages[0].content
    assert response_content, "No generated response was returned"


@then("a StopEvent is present")
def check_stop_event(expert_rag_agent_runner: AgentTestRunner):
    """Check that the agent produced a StopEvent."""
    assert expert_rag_agent_runner.has_stop_event, "Agent did not produce StopEvent"
